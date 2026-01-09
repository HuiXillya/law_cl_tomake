from fastapi import FastAPI, BackgroundTasks, Request
import asyncio
import uuid
import time
import os
import json
import logging
import configparser
from playwright.async_api import async_playwright
import re

logger = logging.getLogger(__name__)

from src.app_func.app_step1_init import _get_all_crawlers
import src.classifier.rule_based_classifier as rule_cls
import src.classifier.llm_based_classifier as llm_cls
from src.string_management import TasksKey, AnnKey, TaskStatus

config = configparser.ConfigParser()
config.read('config.ini')
output_base_path = config.get('Outputdir', 'OUTPUT_PATH', fallback='./output')

llm_enabled = config.getint('LLM', 'llm_classifier', fallback=0) == 1
if llm_enabled:
    classify_dept = llm_cls.classify_dept
else:
    classify_dept = rule_cls.classify_dept

def sanitize_filename(filename: str) -> str:
    """Remove invalid characters for Windows filenames."""
    return re.sub(r'[\\/*?:"<>|]', "_", filename)

async def run_crawlers_step1(task: dict):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        
        crawlers = []
        for crawler_builder in task["selected_crawlers"]:
            crawler = crawler_builder(browser_context=context)
            crawlers.append(crawler)

        async def fetch_safe(crawler):
            try:
                site_announcements = await crawler.fetch_announcements()
                for ann in site_announcements:
                    ann[AnnKey.CRAWLER.value] = crawler
                logger.info(f"Found {len(site_announcements)} announcements from {crawler.__class__.__name__}")
                return site_announcements
            except Exception as e:
                logger.error(f"Error fetching from {crawler.__class__.__name__}: {e}")
                return []

        results = await asyncio.gather(*[fetch_safe(crawler) for crawler in crawlers])
        
        for res in results:
            task[TasksKey.ANNOUNCEMENTS.value].extend(res)
            
        # Cleanup browser references
        for crawler in crawlers:
            crawler.browser = None
            
        await browser.close()

    logger.info(f"Total announcements found: {len(task[TasksKey.ANNOUNCEMENTS.value])}")
    # Filter by target date
    task[TasksKey.STATUS.value] = TaskStatus.SELECTING
    return

async def announcement_crawler_process(tasks_id: str,tasks: dict):
    if tasks_id not in tasks:
        raise ValueError("Invalid task ID")
    # Create output directory
    output_dir = os.path.join(output_base_path+'/',tasks_id)
    os.makedirs(output_dir, exist_ok=True)
    filtered_announcements = tasks[tasks_id][TasksKey.ANNOUNCEMENTS.value]

    step2_tasks = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        
        # Set browser context for all crawlers
        active_crawlers = set()
        crawler_semaphores = {}
        for ann in filtered_announcements:
            crawler = ann.get(AnnKey.CRAWLER.value)
            if crawler and crawler not in active_crawlers:
                crawler.browser = context
                active_crawlers.add(crawler)
                crawler_semaphores[crawler] = asyncio.Semaphore(1)

        try:
            # Process announcements concurrently
            # Note: _single_announcement_crawler_process needs to be async now
            # and we need to gather its results
            
            # Since _single_announcement_crawler_process was doing both crawling AND scheduling classification tasks,
            # we need to split or adapt it. 
            # Let's make _single_announcement_crawler_process async and return the classification task if any.
            
            process_tasks = []
            for idx, ann in enumerate(filtered_announcements):
                crawler = ann.get(AnnKey.CRAWLER.value)
                semaphore = crawler_semaphores.get(crawler)
                process_tasks.append(_single_announcement_crawler_process(idx, ann, output_dir, semaphore))
            
            results = await asyncio.gather(*process_tasks)
            
            # Collect classification tasks from results
            for res in results:
                if res:
                    step2_tasks.append(res)

        finally:
            # Cleanup
            for crawler in active_crawlers:
                crawler.browser = None
            await browser.close()

    # Run classification tasks
    if step2_tasks:
        await asyncio.gather(*step2_tasks)
        
    tasks[tasks_id][TasksKey.STATUS.value] = TaskStatus.STEP3_COMPLETED
    logger.info(f"Crawler completed. Processed {len(filtered_announcements)} announcements.")

async def _single_announcement_crawler_process(idx, ann, output_dir, semaphore=None):
        try:
            # Create attachment folder
            if ann.get(AnnKey.SELECTED.value) is False:
                return None
            attachment_folder = os.path.join(output_dir, "attachments")
            os.makedirs(attachment_folder, exist_ok=True)

            # Parse announcement
            try:
                # Assuming parse_announcement is now async
                title_for_filename = sanitize_filename(ann[AnnKey.TITLE.value])
                if semaphore:
                    async with semaphore:
                        result = await ann[AnnKey.CRAWLER.value].parse_announcement(ann[AnnKey.LINK.value], attachment_folder, default_filename=title_for_filename)
                else:
                    result = await ann[AnnKey.CRAWLER.value].parse_announcement(ann[AnnKey.LINK.value], attachment_folder, default_filename=title_for_filename)
            except Exception as e:
                logger.error(f"Error parsing announcement {ann.get(AnnKey.TITLE.value)}: {e}")
                result = {AnnKey.CONTENT.value: 'None', AnnKey.ATTACHMENTS.value: []}
            
            # Create announcement data
            announcement_data = {
                "日期": ann.get(AnnKey.DATE.value),
                "標題": ann.get(AnnKey.TITLE.value),
                "來源": ann.get(AnnKey.LINK.value),
                "內文": result.get(AnnKey.CONTENT.value),
                "附件名稱": result.get(AnnKey.ATTACHMENTS.value)
            }
            
            # Save to JSON files
            filename = f"{idx+1:08d}.json"
            filepath = os.path.join(output_dir, filename)
            # Use aiofiles for async file I/O if possible, but standard open is okay for small files in this context
            # or run in executor. For now, keep it simple as JSON dump is fast.
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(announcement_data, f, ensure_ascii=False, indent=2)

            # Classify department
            attachment_paths = [os.path.join(attachment_folder, att) for att in result.get(AnnKey.ATTACHMENTS.value, [])]
            
            # Update ann object
            ann[AnnKey.CONTENT.value] = result.get(AnnKey.CONTENT.value)
            ann[AnnKey.ATTACHMENTS.value] = result.get(AnnKey.ATTACHMENTS.value, [])
            
            # Return the coroutine for classification to be run later
            return _single_classify_dept((ann.get(AnnKey.TITLE.value), result.get(AnnKey.CONTENT.value), attachment_paths), ann)
            
        except Exception as e:
            logger.error(f"Error processing announcement {ann.get(AnnKey.TITLE.value)}: {e}")
            return None
async def _single_classify_dept(inputs, ann):
    if not inputs:
        return
    try:
        dept_set = await classify_dept(*inputs)
        ann[AnnKey.DEPARTMENTS.value] = list(dept_set)
    except Exception as e:
        ann[AnnKey.DEPARTMENTS.value] = []
        logger.error(f"Error classifying announcement {ann.get(AnnKey.TITLE.value)}: {e}")
async def _my_gatterer(tasks):
    return await asyncio.gather(*tasks)