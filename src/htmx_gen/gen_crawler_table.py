
from src.string_management import URLS, TasksKey
from src.base_crawler import BaseCrawler

def gen_crawler_table(crawler_list: list[BaseCrawler], disable_crawlers: list[BaseCrawler]):
    text_rows = []
    for crawler in crawler_list:
        cl_name = crawler.__name__
        display_name = crawler.DISPLAY_NAME 

        if crawler in disable_crawlers:
            text = f"""
                <li>
                    <label for="{cl_name}"><del>{display_name}</del></label>
                    <ul>
                        <li><del>網址: {crawler.BASE_URL}</del></li>
                    </ul>
                </li>
            """
        else:
            checked = 'checked="blue"' if True else ''
            text = f"""
                <li>
                    <input type="checkbox" id="check_box_{cl_name}" name="selectedOptions" value="{cl_name}" {checked}/>
                    <label for="{cl_name}">{display_name}</label>
                    <ul>
                        <li>網址: {crawler.BASE_URL}</li>
                    </ul>
                </li>
            """
        text_rows.append(text)

    return f"""
    <form hx-post="{URLS.STEP1_SET_ENABLE_CRAWLERS.value}" 
        hx-trigger="submit"
        hx-swap="none">
        <button type="submit">開始爬取</button>
        <ul id="myCheckboxList">
            {''.join(text_rows)}
        </ul>
    </form>
    """