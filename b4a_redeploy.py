import os
import base64
import sys
import requests
from nacl.encoding import Base64Encoder
from nacl.public import PublicKey, SealedBox
from seleniumbase import SB

CONNECT_SID = os.environ.get("CONNECT_SID", "s%3Aq19aYI4eTRmy2d2YoSuqSVZZ16KnP6sb.JoBg8enE6dZKY3HzMz6XmqSJPiULD5ydVo3y0xJl7is")
GH_TOKEN = os.environ.get("GH_TOKEN", "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")
GH_REPO = os.environ.get("GITHUB_REPOSITORY", "")

APP_ID = "d54d86c4-1cc3-48a0-b7f7-169fffc36d78"  # 替换成你自己的 Back4App App ID
APP_URL = f"https://containers.back4app.com/apps/{APP_ID}"
PROXY = ""

def log(msg):
    print(msg)

def update_github_secret(secret_name, secret_value):
    if not GH_TOKEN or not GH_REPO:
        log("GH_TOKEN or GITHUB_REPOSITORY not available, skipping secret update")
        return False
    try:
        headers = {
            "Authorization": f"token {GH_TOKEN}",
            "Accept": "application/vnd.github.v3+json"
        }
        pk_resp = requests.get(
            f"https://api.github.com/repos/{GH_REPO}/actions/secrets/public-key",
            headers=headers,
            timeout=10
        )
        pk_resp.raise_for_status()
        pk_data = pk_resp.json()

        public_key = PublicKey(pk_data["key"].encode(), encoder=Base64Encoder)
        sealed_box = SealedBox(public_key)
        encrypted = sealed_box.encrypt(secret_value.encode())
        encrypted_b64 = base64.b64encode(encrypted).decode()

        put_resp = requests.put(
            f"https://api.github.com/repos/{GH_REPO}/actions/secrets/{secret_name}",
            headers=headers,
            json={
                "encrypted_value": encrypted_b64,
                "key_id": pk_data["key_id"]
            },
            timeout=10
        )
        put_resp.raise_for_status()
        log(f"GitHub secret '{secret_name}' updated successfully")
        return True
    except Exception as e:
        log(f"Failed to update GitHub secret: {e}")
        return False

def run():
    with SB(uc=True, headless=True, proxy=PROXY, window_size="1920,1080") as sb:
        log("Opening back4app.com to set cookie...")
        sb.open("https://www.back4app.com")
        sb.wait_for_ready_state_complete()

        sb.driver.execute_cdp_cmd("Network.setCookie", {
            "name": "connect.sid",
            "value": CONNECT_SID,
            "domain": ".back4app.com",
            "path": "/",
            "secure": True,
            "httpOnly": True,
            "sameSite": "Lax"
        })
        log("Cookie injected to .back4app.com")

        log("跳转到目标 App 页面...")
        sb.open(APP_URL)
        sb.wait_for_element_present("body", timeout=15)

        current_url = sb.get_current_url()
        log(f"当前 URL: {current_url}")

        if "login" in current_url.lower():
            msg = "❌ Cookie 已失效，已被重定向到登录页，请手动更新 CONNECT_SID secret"
            log(msg)
            raise Exception(msg)

        if APP_ID not in current_url:
            sb.save_screenshot("wrong_page.png")
            msg = f"❌ 未到达目标 App 页面，当前 URL: {current_url}"
            log(msg)
            raise Exception(msg)

        log("✅ 成功进入目标 app 页面")

        # 检查服务器是否刷新了 connect.sid
        try:
            result = sb.driver.execute_cdp_cmd("Network.getAllCookies", {})
            cookies = result.get("cookies", [])
            for cookie in cookies:
                if cookie["name"] == "connect.sid" and cookie["value"] != CONNECT_SID:
                    log("Detected updated connect.sid, updating GitHub secret...")
                    new_sid = cookie["value"]
                    update_github_secret("CONNECT_SID", new_sid)
                    break
        except Exception as e:
            log(f"⚠️ 跳过检查 Cookie: {e}")

        log("检查应用当前运行状态...")
        is_available = False
        try:
            sb.wait_for_text("Available", timeout=10)
            is_available = True
        except Exception:
            pass

        if is_available:
            msg = "✅ 检测到 'Available' 状态，程序正在正常运行，无需重新部署。"
            log(msg)
            return

        log("未处于 Available 状态，准备执行重新部署...")
        sb.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        redeploy_index = None
        redeploy_text = None

        for attempt in range(15):
            buttons = sb.find_elements("button")
            for i, btn in enumerate(buttons):
                if "redeploy" in btn.text.lower():
                    redeploy_index = i
                    redeploy_text = btn.text.strip()
                    break
            if redeploy_index is not None:
                break
            sb.sleep(1)

        if redeploy_index is None:
            sb.save_screenshot("button_not_found.png")
            msg = "❌ 未找到 Redeploy 按钮。可能页面结构已变化或不在可部署状态。"
            log(msg)
            raise Exception(msg)

        log(f"✅ 找到重部署按钮: '{redeploy_text}' at index {redeploy_index}, 点击中...")

        sb.execute_script(
            "var btns = document.querySelectorAll('button');"
            f"btns[{redeploy_index}].scrollIntoView(true);"
            f"btns[{redeploy_index}].click();"
        )

        log("⏳ 检查按钮是否消失...")
        click_confirmed = False
        for i in range(5):
            sb.sleep(3)
            log(f"尝试 {i+1}/5 ...")
            btn_exists = False
            current_buttons = sb.find_elements("button")
            for btn in current_buttons:
                if "redeploy" in btn.text.lower():
                    btn_exists = True
                    break
            if not btn_exists:
                click_confirmed = True
                break

        sb.save_screenshot("after_click.png")
        log("📸 Screenshot saved: after_click.png")

        if click_confirmed:
            msg = "🎉 Redeploy 成功，部署按钮已消失，Console 正在显示部署日志"
        else:
            msg = "⚠️ 已点击 Redeploy 按钮，但按钮未消失，请查看截图手动核对"
        log(msg)

if __name__ == "__main__":
    try:
        run()
    except Exception as e:
        err = f"❌ 脚本出错: {e}"
        print(err)
        sys.exit(1)
