from playwright.sync_api import sync_playwright, expect
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
    page=browser.new_page(viewport={'width':412,'height':915});errors=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.on('console',lambda m:errors.append(m.text) if m.type=='error' and 'Failed to load resource' not in m.text else None)
    page.add_init_script("localStorage.setItem('pulse_onboarded','1');localStorage.setItem('pulse_api','http://127.0.0.1:8011');")
    page.goto('http://127.0.0.1:8082/product/fixture')
    expect(page.get_by_text('LOWEST FRESH EXACT LISTING',exact=True)).to_be_visible(timeout=15000)
    assert page.get_by_text('Verified exact match',exact=True).count()==2
    page.get_by_role('button',name='Save product',exact=True).click()
    expect(page.get_by_role('button',name='Saved to watchlist',exact=True)).to_be_visible()
    page.get_by_role('button',name='Retailer detail',exact=True).click()
    expect(page.get_by_text('Consider waiting',exact=True)).to_be_visible(timeout=15000)
    page.get_by_label('Target price in rupees',exact=True).fill('8500.00')
    page.get_by_role('button',name='Save price target',exact=True).click()
    expect(page.get_by_text('Target saved',exact=True)).to_be_visible()
    page.get_by_role('button',name='7 days',exact=True).click()
    expect(page.get_by_text('Insufficient data',exact=True)).to_be_visible(timeout=15000)
    page.get_by_role('button',name='All available',exact=True).click()
    expect(page.get_by_text('Consider waiting',exact=True)).to_be_visible(timeout=15000)
    page.screenshot(path='artifacts/product-isolated-test-fixture.png',full_page=True)
    page.get_by_role('button',name='Saved',exact=True).click()
    expect(page.get_by_text('TEST FIXTURE handset - not a real product',exact=True).filter(visible=True)).to_be_visible(timeout=15000)
    page.get_by_role('button',name='Open alerts',exact=True).click()
    expect(page.get_by_text('Target reached',exact=True)).to_be_visible(timeout=15000)
    assert not errors,errors
    print('PASS: isolated synthetic test server only: exact comparison, separate retailer history, range statistics/recommendations, saving, target alert and navigation; no runtime errors.')
    browser.close()
