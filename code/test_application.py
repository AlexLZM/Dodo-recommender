import os, sys
sys.path.append(os.path.abspath('../scraper'))
sys.path.append(os.path.abspath('../scraper/brandoff'))
sys.path.append(os.path.abspath('../scraper/amore'))
sys.path.append(os.path.abspath('../scraper/daikokuya'))
sys.path.append(os.path.abspath('../scraper/luxurygaragesale'))
sys.path.append(os.path.abspath('../scraper/qoo'))
from app import application
import amore_func
import bd_func
import daikokuya_func
import lgs_func
import qoo_func

def test_application():
    '''
    test the overall application
    '''
    assert application is not None

def test_amore():
    '''
    test bd scraper
    '''
    string_with_numbers = 'teststring123'
    assert amore_func.hasNumbers(string_with_numbers) is True

    string_without_numbers = 'teststring'
    assert amore_func.hasNumbers(string_without_numbers) is False

def test_bd():
    '''
    test bd scraper
    '''
    expected_sku = '12345678'
    url_with_sku = 'https://test.com/detail.asp?scode=' + expected_sku
    assert bd_func.get_item_sku(url_with_sku) == expected_sku

    url_without_sku = 'https://test.com/test'
    assert bd_func.get_item_sku(url_without_sku) == "N/A"

def test_daikokuya():
    '''
    test daikokuya scraper
    '''
    expected_sku = '12345678'
    url_with_sku = 'https://test.com/' + expected_sku + '.html'
    assert daikokuya_func.get_item_sku(url_with_sku) == expected_sku

    url_without_sku = None
    assert daikokuya_func.get_item_sku(url_without_sku) == "N/A"

def test_luxurygaragesale():
    '''
    test luxurygaragesale scraper
    '''
    expected_sku = '12345678'
    url_with_sku = 'https://test.com/test-' + expected_sku
    assert lgs_func.get_item_sku(url_with_sku) == expected_sku

    url_without_sku = None
    assert lgs_func.get_item_sku(url_without_sku) == "N/A"

def test_qoo():
    '''
    test the qoo scraper
    '''
    expected_sku = '12345678'
    url_with_sku = 'https://test.com/?' + expected_sku
    assert qoo_func.get_item_sku(url_with_sku) == expected_sku

    url_without_sku = None
    assert qoo_func.get_item_sku(url_without_sku) == "N/A"