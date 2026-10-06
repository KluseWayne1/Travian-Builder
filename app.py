from flask import Flask, render_template, request, jsonify
import requests
from bs4 import BeautifulSoup
import threading
import time
import re
import random

app = Flask(__name__)

req_lock = threading.RLock()

bot_session = requests.Session()
bot_session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9,fa;q=0.8',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1'
})

bot_config = {
    "username": "",
    "password": "",
    "server_url": "",
    "is_logged_in": False
}

villages = {}

BUILDING_NAMES = {
    1: "هیزم شکن", 2: "آجرسازی", 3: "معدن آهن", 4: "گندم زار",
    5: "چوب بری", 6: "آجر پزی", 7: "ذوب‌ آهن", 8: "آسیاب", 9: "نانوایی",
    10: "انبار", 11: "انبار غذا", 12: "آهنگری", 13: "اسلحه سازی", 14: "میدان تمرین",
    15: "ساختمان اصلی", 16: "اردوگاه", 17: "بازار", 18: "سفارت", 19: "سربازخانه",
    20: "اصطبل", 21: "کارگاه", 22: "دارالفنون", 23: "مخفیگاه", 24: "تالار",
    25: "اقامتگاه", 26: "قصر", 27: "خزانه", 28: "عمارت بازرگانی", 29: "پادگان بزرگ",
    30: "اصطبل بزرگ", 31: "شهرداری", 32: "دیوار گلی", 33: "دیوار چوبی", 34: "سنگر",
    35: "آبجوسازی", 36: "تله‌ساز", 37: "عمارت قهرمان", 38: "انبار بزرگ", 39: "انبار غذای بزرگ",
    40: "شگفتی جهان", 41: "آبشخور اسب", 42: "کتیبه‌ها", 44: "دارالفنون", 45: "بیمارستان"
}

def is_session_valid(soup, url):
    current_url = url.rstrip('/')
    server_root = bot_config['server_url'].rstrip('/')
    
    if "login.php" in current_url or current_url == server_root: 
        return False
    if soup.find('input', {'type': 'password'}) or soup.find('input', {'name': 'password'}): 
        return False
    if soup.find(id='l1'): 
        return True
    if soup.find('a', href=lambda x: x and 'logout.php' in x): 
        return True
    if soup.find(class_='stockContainer'): 
        return True 
    
    return False

def scrape_resources(soup):
    resources = {"wood": 0, "clay": 0, "iron": 0, "crop": 0}
    try:
        def get_val(id_str):
            el = soup.find(id=id_str)
            if el:
                val = re.sub(r'\D', '', el.text)
                return int(val) if val else 0
            return 0
        resources["wood"] = get_val('l1')
        resources["clay"] = get_val('l2')
        resources["iron"] = get_val('l3')
        resources["crop"] = get_val('l4')
    except: 
        pass
    return resources

def scrape_real_queue(soup):
    queue = []
    try:
        b_list = soup.find('div', class_='buildingList')
        if b_list:
            items = b_list.find_all('li')
            for item in items:
                name_div = item.find('div', class_='name')
                timer_span = item.find('span', class_='movTimer') or item.find('span', class_='timer')
                if name_div:
                    full_text = re.sub(r'\s+', ' ', name_div.text.strip().replace('\n', ' '))
                    lvl = 0
                    match = re.search(r'سطح\s+(\d+)', full_text)
                    if match: 
                        lvl = int(match.group(1))
                    timer = timer_span.text.strip() if timer_span else "در حال ساخت..."
                    queue.append({"text": full_text, "level": lvl, "timer": timer})
    except: 
        pass
    return queue

def login_to_travian():
    global bot_session
    if not bot_config["server_url"]: 
        return False
        
    base_url = bot_config['server_url'].replace('/login.php', '').rstrip('/')
    login_url = f"{base_url}/login.php"
    
    try:
        with req_lock:
            new_session = requests.Session()
            new_session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9,fa;q=0.8',
                'Connection': 'keep-alive'
            })
            
            res = new_session.get(login_url, timeout=10)
            soup = BeautifulSoup(res.text, 'html.parser')
            
            form = None
            for f in soup.find_all('form'):
                if f.find('input', {'type': 'password'}) or f.find('input', {'name': 'password'}):
                    form = f
                    break
            if not form: 
                form = soup.find('form')
            
            login_data = {}
            if form:
                for inp in form.find_all('input'):
                    if inp.get('name'): 
                        login_data[inp.get('name')] = inp.get('value', '')
                        
            login_data.update({'name': bot_config["username"], 'password': bot_config["password"]})
            if 's1' not in login_data: 
                login_data['s1'] = 'Login'
                
            time.sleep(random.uniform(1.5, 3.5))
            post_res = new_session.post(login_url, data=login_data, timeout=10)
            soup_post = BeautifulSoup(post_res.text, 'html.parser')
            
            if is_session_valid(soup_post, post_res.url):
                bot_config["is_logged_in"] = True
                bot_config["server_url"] = base_url
                bot_session = new_session
                print("[AUTH] Login successful. Session restored.", flush=True)
                return True
        return False
    except Exception as e: 
        print(f"[AUTH] Failed: {e}", flush=True)
        return False

def update_village_data(vid):
    v_data = villages.get(vid)
    if not v_data: 
        return False
    server_url = bot_config['server_url'].rstrip('/')
    
    try:
        with req_lock:
            if vid and str(vid) != "default":
                r1 = bot_session.get(f"{server_url}/dorf1.php?newdid={vid}", timeout=10)
            else:
                r1 = bot_session.get(f"{server_url}/dorf1.php", timeout=10)
                
            soup1 = BeautifulSoup(r1.text, 'html.parser')
            
            if not is_session_valid(soup1, r1.url):
                if login_to_travian():
                    if vid and str(vid) != "default":
                        r1 = bot_session.get(f"{server_url}/dorf1.php?newdid={vid}", timeout=10)
                    else:
                        r1 = bot_session.get(f"{server_url}/dorf1.php", timeout=10)
                    soup1 = BeautifulSoup(r1.text, 'html.parser')
                else: 
                    return False
                
            time.sleep(random.uniform(0.5, 1.2))
            
            r2 = bot_session.get(f"{server_url}/dorf2.php", timeout=10)
            soup2 = BeautifulSoup(r2.text, 'html.parser')
            
        token_match = re.search(r'token[\'"]?\s*:\s*[\'"]([a-zA-Z0-9]+)[\'"]', r1.text)
        v_data["token"] = token_match.group(1) if token_match else ""
        
        extracted_resources = scrape_resources(soup1)
        extracted_queue = scrape_real_queue(soup1)
        
        buildings = []
        for soup in [soup1, soup2]:
            slots = soup.find_all(attrs={"data-aid": True})
            for slot in slots:
                try:
                    aid_raw = slot.get("data-aid")
                    if not aid_raw or not str(aid_raw).isdigit(): 
                        continue
                    aid = int(aid_raw)
                    
                    gid_raw = slot.get("data-gid")
                    gid = 0
                    if gid_raw and str(gid_raw).isdigit(): 
                        gid = int(gid_raw)
                    else:
                        for c in slot.get("class", []):
                            if isinstance(c, str) and c.startswith("g") and c[1:].isdigit():
                                gid = int(c[1:])
                                break
                    
                    level_el = slot.find(class_='labelLayer') or slot.find(class_='level')
                    level = 0
                    if level_el:
                        lvl_text = re.sub(r'\D', '', level_el.text)
                        if lvl_text: 
                            level = int(lvl_text)
                            
                    name = BUILDING_NAMES.get(gid, f"ناشناخته ({gid})") if gid != 0 else "مکان خالی"
                    buildings.append({"aid": aid, "gid": gid, "name": name, "level": level})
                except: 
                    continue

        if buildings:
            unique_buildings = {b["aid"]: b for b in buildings}
            v_data["buildings"] = [unique_buildings[k] for k in sorted(unique_buildings.keys())]
            
        v_data["resources"] = extracted_resources
        v_data["real_queue"] = extracted_queue
        
        return True
    except Exception:
        return False

def cleanup_bot_queue(vid):
    v_data = villages.get(vid)
    if not v_data: 
        return
    
    new_q = []
    matched_rq_indices = set()
    
    for bq in v_data["bot_queue"]:
        b_level = next((b['level'] for b in v_data["buildings"] if b['aid'] == bq['aid']), 0)
        if b_level >= bq['target_level']: 
            continue
            
        in_real = False
        for i, rq in enumerate(v_data["real_queue"]):
            if i not in matched_rq_indices and bq['name'] in rq['text'] and rq['level'] == bq['target_level']:
                in_real = True
                matched_rq_indices.add(i)
                break
                
        if not in_real:
            new_q.append(bq)
        
    v_data["bot_queue"] = new_q

def execute_build(vid, aid):
    if not bot_config["server_url"]: 
        return False
        
    server_url = bot_config['server_url'].rstrip('/')
    dorf = "dorf1.php" if int(aid) <= 18 else "dorf2.php"
    
    if vid and str(vid) != "default":
        with req_lock: 
            r_switch = bot_session.get(f"{server_url}/dorf1.php?newdid={vid}", timeout=10)
            soup_sw = BeautifulSoup(r_switch.text, 'html.parser')
            if not is_session_valid(soup_sw, r_switch.url): 
                return False
            time.sleep(random.uniform(0.5, 1.2)) 
            
    build_url = f"{server_url}/build.php?id={aid}"
    
    try:
        with req_lock: 
            res = bot_session.get(build_url, timeout=10)
            
        time.sleep(random.uniform(1.0, 2.5))
        soup = BeautifulSoup(res.text, 'html.parser')
        upgrade_link = None
        
        for btn in soup.find_all(['button', 'a']):
            onclick = btn.get('onclick', '')
            if onclick and f'?a={aid}' in onclick and '&c=' in onclick:
                match = re.search(r"[\"']([^\"']*?\?a=\d+&c=[a-zA-Z0-9]+)[\"']", onclick)
                if match:
                    upgrade_link = match.group(1)
                    break
                    
        if not upgrade_link:
            for link in soup.find_all('a', href=True):
                href = link.get('href', '')
                if f'?a={aid}' in href and '&c=' in href:
                    upgrade_link = href
                    break
                    
        if not upgrade_link:
            html_str = str(soup)
            match = re.search(rf"[\"']([^\"']*?\?a={aid}&c=[a-zA-Z0-9]+)[\"']", html_str)
            if match: 
                upgrade_link = match.group(1)
                    
        if upgrade_link:
            target_url = f"{server_url}/{dorf}{upgrade_link}" if upgrade_link.startswith('?') else f"{server_url}/{upgrade_link}"
            target_url = target_url.replace(f"{server_url}//", f"{server_url}/")
            with req_lock: 
                bot_session.get(target_url, timeout=10)
            return True
            
        return False
    except: 
        return False

def fire_gold(server_url, token):
    try:
        with req_lock:
            headers = {
                "Content-Type": "application/json", 
                "X-Requested-With": "XMLHttpRequest",
                "Origin": server_url,
                "Referer": f"{server_url}/dorf1.php"
            }
            if token: 
                headers["Authorization"] = f"Bearer {token}"
                
            payload = {"action": "premiumFeature"}
            api_url = f"{server_url}/api/v1/premium/instant-completion"
            
            bot_session.put(api_url, json=payload, headers=headers, timeout=10)
            time.sleep(random.uniform(0.3, 0.7))
            bot_session.post(api_url, json=payload, headers=headers, timeout=10)
            return True
    except: 
        return False

def bot_background_loop():
    last_keepalive = time.time()
    while True:
        try:
            if not bot_config["is_logged_in"]:
                time.sleep(2)
                continue
                
            now = time.time()
            server_url = bot_config['server_url'].rstrip('/')
            
            if now - last_keepalive > 800: 
                try:
                    with req_lock:
                        test = bot_session.get(f"{server_url}/dorf1.php", timeout=10)
                        soup_test = BeautifulSoup(test.text, 'html.parser')
                        if not is_session_valid(soup_test, test.url):
                            login_to_travian()
                    last_keepalive = time.time()
                except: 
                    pass
            
            for vid, v_data in list(villages.items()):
                if not v_data.get("bot_active", False):
                    continue
                
                is_random = v_data.get("build_random_mode", True)
                current_build_interval = v_data.get("current_random_interval", random.randint(10, 30)) if is_random else v_data.get("build_interval", 15)
                
                if (now - v_data.get("last_build_check", 0)) >= current_build_interval:
                    v_data["last_build_check"] = time.time()
                    if is_random: 
                        v_data["current_random_interval"] = random.randint(10, 30)
                        
                    data_updated = update_village_data(vid)
                    
                    if data_updated:
                        cleanup_bot_queue(vid)
                        bot_q_len = len(v_data["bot_queue"])
                        
                        if bot_q_len == 1:
                            if len(v_data.get("real_queue", [])) < 2:
                                time.sleep(random.uniform(1.2, 2.5))
                                if execute_build(vid, v_data["bot_queue"][0]["aid"]):
                                    time.sleep(random.uniform(1.5, 3.0))
                                    update_village_data(vid)
                                    
                        elif bot_q_len >= 2:
                            builds_done = 0
                            while len(v_data.get("real_queue", [])) < 2 and len(v_data["bot_queue"]) > 0 and builds_done < 2:
                                time.sleep(random.uniform(1.2, 2.5))
                                if execute_build(vid, v_data["bot_queue"][0]["aid"]):
                                    time.sleep(random.uniform(1.5, 3.0))
                                    update_village_data(vid)
                                    cleanup_bot_queue(vid)
                                    builds_done += 1
                                else:
                                    break
                            
                            if v_data.get("gold_active") and len(v_data.get("real_queue", [])) >= 2:
                                time.sleep(random.uniform(2.5, 4.5)) 
                                fire_gold(server_url, v_data.get("token", ""))
                                time.sleep(random.uniform(1.5, 2.5))
                                update_village_data(vid)
                                
                time.sleep(random.uniform(1.5, 3.5))
                
        except Exception:
            pass
            
        time.sleep(2) 

threading.Thread(target=bot_background_loop, daemon=True).start()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/status', methods=['GET'])
def api_status():
    return jsonify({
        "is_logged_in": bot_config["is_logged_in"],
        "server": bot_config["server_url"],
        "username": bot_config["username"]
    })

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.json
    if bot_config["is_logged_in"] and bot_config["username"] == data.get("username", "").strip():
        return jsonify({"success": True, "message": "Already logged in globally."})
        
    bot_config.update({
        "server_url": data.get("server", "").strip(),
        "username": data.get("username", "").strip(),
        "password": data.get("password", "").strip()
    })
    return jsonify({"success": login_to_travian()})

@app.route('/api/logout', methods=['POST'])
def api_logout():
    global bot_session, bot_config, villages
    bot_session = requests.Session()
    bot_session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)',
    })
    bot_config = {"username": "", "password": "", "server_url": "", "is_logged_in": False}
    villages = {}
    return jsonify({"success": True})

@app.route('/api/fetch_game_data', methods=['GET'])
def fetch_game_data():
    if not bot_config["is_logged_in"]: 
        return jsonify({"error": "وارد نشده‌اید"}), 401
        
    try:
        server_url = bot_config['server_url'].rstrip('/')
        with req_lock:
            res = bot_session.get(f"{server_url}/dorf1.php", timeout=10)
            soup_res = BeautifulSoup(res.text, 'html.parser')
            if not is_session_valid(soup_res, res.url):
                if login_to_travian():
                    res = bot_session.get(f"{server_url}/dorf1.php", timeout=10)
                    soup_res = BeautifulSoup(res.text, 'html.parser')
        
        extracted_villages = []
        for el in soup_res.find_all(attrs={"data-did": True}):
            did = el.get("data-did")
            name_div = el.find(class_='name')
            name = name_div.text.strip() if name_div else " ".join(el.text.split())
            if name and did and not any(v['id'] == did for v in extracted_villages):
                extracted_villages.append({"id": did, "name": name})

        if not extracted_villages:
            valid_vids = [vid for vid in villages.keys() if vid != "default"]
            if valid_vids:
                for vid in valid_vids:
                    extracted_villages.append({"id": vid, "name": villages[vid]["name"]})
            else:
                extracted_villages = [{"id": "default", "name": "دهکده اصلی"}]

        is_first = True
        for v in extracted_villages:
            if v["id"] not in villages:
                villages[v["id"]] = {
                    "name": v["name"], 
                    "resources": {}, 
                    "buildings": [],
                    "real_queue": [], 
                    "bot_queue": [], 
                    "bot_active": False,  
                    "build_interval": 15,
                    "build_random_mode": True,
                    "current_random_interval": random.randint(10, 30),
                    "gold_active": False,
                    "last_build_check": 0,
                    "is_capital": is_first,
                    "token": ""
                }
            is_first = False

        return jsonify({"success": True, "villages": extracted_villages})
    except Exception as e: 
        return jsonify({"error": str(e)}), 500

@app.route('/api/change_village/<vid>', methods=['GET'])
def change_village(vid):
    if not bot_config["is_logged_in"]: 
        return jsonify({"error": "وارد نشده‌اید"}), 401
    
    update_village_data(vid)
    cleanup_bot_queue(vid)
    v_data = villages.get(vid, {})
    
    settings = {
        "bot_active": v_data.get("bot_active", False),
        "build_interval": v_data.get("build_interval", 15),
        "build_random_mode": v_data.get("build_random_mode", True),
        "gold_active": v_data.get("gold_active", False),
        "is_capital": v_data.get("is_capital", False)
    }
    return jsonify({
        "success": True, 
        "resources": v_data.get("resources", {}), 
        "buildings": v_data.get("buildings", []), 
        "bot_queue": v_data.get("bot_queue", []), 
        "real_queue": v_data.get("real_queue", []), 
        "settings": settings
    })

@app.route('/api/get_cache/<vid>', methods=['GET'])
def get_cache(vid):
    if not bot_config["is_logged_in"]: 
        return jsonify({"error": "Unauthorized"}), 401
        
    v_data = villages.get(vid)
    if not v_data: 
        return jsonify({"error": "Not found"}), 404
        
    return jsonify({
        "success": True,
        "resources": v_data.get("resources", {}),
        "buildings": v_data.get("buildings", []),
        "bot_queue": v_data.get("bot_queue", []),
        "real_queue": v_data.get("real_queue", [])
    })

@app.route('/api/village/<vid>/queue', methods=['POST', 'DELETE'])
def manage_queue(vid):
    if vid in villages:
        if request.method == 'POST':
            item = request.json.get("item")
            curr_lvl = int(item.get("current_level"))
            tgt_lvl = int(item.get("target_level"))
            
            is_cap = villages[vid].get("is_capital", False)
            max_allowed = 20
            if int(item["aid"]) <= 18 and not is_cap:
                max_allowed = 10
                
            tgt_lvl = min(tgt_lvl, max_allowed)
            
            if tgt_lvl > curr_lvl:
                for lvl in range(curr_lvl + 1, tgt_lvl + 1):
                    villages[vid]["bot_queue"].append({"aid": item["aid"], "name": item["name"], "target_level": lvl})
        elif request.method == 'DELETE':
            villages[vid]["bot_queue"] = []
            
        return jsonify({"success": True, "bot_queue": villages[vid]["bot_queue"]})
    return jsonify({"error": "دهکده یافت نشد"}), 404

@app.route('/api/village/<vid>/upgrade_all_resources', methods=['POST'])
def upgrade_all_resources(vid):
    if vid in villages:
        v_data = villages[vid]
        is_cap = v_data.get("is_capital", False)
        target_lvl = 20 if is_cap else 10
        
        for b in v_data.get("buildings", []):
            if 1 <= b["aid"] <= 18:
                curr_lvl = b["level"]
                
                highest_in_queue = curr_lvl
                for q in v_data["bot_queue"]:
                    if q["aid"] == b["aid"] and q["target_level"] > highest_in_queue:
                        highest_in_queue = q["target_level"]
                        
                if highest_in_queue < target_lvl:
                    for lvl in range(highest_in_queue + 1, target_lvl + 1):
                        v_data["bot_queue"].append({
                            "aid": b["aid"], 
                            "name": b["name"], 
                            "target_level": lvl
                        })
                        
        return jsonify({"success": True, "bot_queue": v_data["bot_queue"]})
    return jsonify({"error": "دهکده یافت نشد"}), 404

@app.route('/api/village/<vid>/settings', methods=['POST'])
def update_settings(vid):
    if vid in villages:
        data = request.json
        villages[vid]["bot_active"] = bool(data.get("bot_active", False)) 
        villages[vid]["build_interval"] = int(data.get("build_interval", 15))
        villages[vid]["build_random_mode"] = bool(data.get("build_random_mode", True))
        villages[vid]["gold_active"] = bool(data.get("gold_active", False))
        villages[vid]["is_capital"] = bool(data.get("is_capital", False))
        return jsonify({"success": True})
    return jsonify({"error": "دهکده یافت نشد"}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=False)