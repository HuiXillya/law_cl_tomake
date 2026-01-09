import logging
import configparser

logger = logging.getLogger(__name__)

from src.htmx_gen.gen_crawler_table import gen_crawler_table
from src.crawlers import (
    FSC_Crawler,
    SFB_Crawler,
    CentralBankFX_Crawler,
    CentralBank_Crawler,
    CentralBankLaw_Crawler,
    TWSE_Crawler,
    TWSE_dsp_Crawler,
    TWSE_announcement_Crawler,
    TPEx_Crawler,
    TAIFEX_Crawler,
    LawBank_Crawler,
    TWSA_Crawler,
    TFutures_Crawler,
    TDCC_Crawler,
    MOJ_Law_Crawler,
    GAZETTE_Crawler,
    BankingLaw_Crawler,
    Law_Lib_Crawler,
    Trust_Crawler,
    SELAW_Crawler,
    # Add other crawlers as they are implemented
)

def _get_all_crawlers():
    """
    Returns a list of all available crawler classes.
    """
    return [
        FSC_Crawler,
        SFB_Crawler,
        CentralBankFX_Crawler,
        CentralBank_Crawler,
        CentralBankLaw_Crawler,
        TWSE_Crawler,
        TWSE_dsp_Crawler,
        TWSE_announcement_Crawler,
        TPEx_Crawler,
        TAIFEX_Crawler,
        LawBank_Crawler,
        TWSA_Crawler,
        TFutures_Crawler,
        TDCC_Crawler,
        MOJ_Law_Crawler,
        GAZETTE_Crawler,
        BankingLaw_Crawler,
        Law_Lib_Crawler,
        Trust_Crawler,
        SELAW_Crawler,
        # Add other crawlers here as implemented
    ]
def step1_init():
    cl_list = _get_all_crawlers()
    disable_crawlers = []
    config = configparser.ConfigParser()
    config.read('config.ini')
    if config.has_section('DisableCrawlers'):
        disable_crawlers_names = [name.strip() for name in config.options('DisableCrawlers') if config.getboolean('DisableCrawlers', name)]
    for crawler_cls in cl_list:
        if crawler_cls.__name__.lower() in disable_crawlers_names:
            disable_crawlers.append(crawler_cls)
    htmx = gen_crawler_table(cl_list,disable_crawlers)
    return htmx
def _main():
    html = step1_init()
    logger.debug(html)

