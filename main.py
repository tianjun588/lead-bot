import os
import sys
import time
import hashlib
import subprocess
import requests

# ==========================================
# 1. 核心风控参数与云端鉴权
# ==========================================
CF_WORKER_URL = "https://nexus-auth.xiaozhuanfeng0.workers.dev"
SALT = "NEXUS_CORE_SALT_888"  # 混淆盐，防止主板明文裸奔

def get_machine_code():
    """提取物理主板 UUID，重装系统也不会变的终极指纹"""
    try:
        # 调用 Windows 原生 wmic 命令获取主板标识，脱离对第三方库的依赖
        output = subprocess.check_output('wmic csproduct get uuid', shell=True).decode().split('\n')[1].strip()
        # 加盐 MD5 混淆
        return hashlib.md5((output + SALT).encode('utf-8')).hexdigest().upper()
    except Exception:
        print("[!] 致命错误：无法读取设备物理指纹，请尝试右键以管理员身份运行。")
        sys.exit(1)

def verify_license():
    """云端卡密强校验拦截网"""
    print("=" * 50)
    print(" NEXUS 商业获客雷达 v2.0 - 终端安全鉴权")
    print("=" * 50)
    
    # 实际 GUI 版可以改由 Eel 界面传参，目前用终端输入流测试
    user_key = input("请输入商业授权码 (测试请用 NEXUS-VIP-888): ").strip()
    mac_code = get_machine_code()
    
    print(f"[*] 本机物理主板指纹: {mac_code}")
    print("[*] 正在连接边缘计算节点核验授权...")
    
    try:
        res = requests.post(
            CF_WORKER_URL, 
            json={"key": user_key, "machine_code": mac_code},
            timeout=10
        ).json()
        
        if res.get("code") == 200:
            print(f"[+] 鉴权通过！{res.get('msg')}")
            return True
        else:
            print(f"[-] 鉴权拦截！{res.get('msg')}")
            time.sleep(5)
            sys.exit(1)
    except Exception as e:
        print("[-] 无法连接鉴权服务器！请检查网络是否通畅或被本地杀软/防火墙拦截。")
        time.sleep(5)
        sys.exit(1)

# ==========================================
# 2. 浏览器环境隔离与容灾自愈
# ==========================================
def get_safe_cache_dir():
    """抛弃 %TEMP%，在同级目录建立隐藏隔离缓存区，防止被360等管家清空导致账号掉线"""
    base_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
    cache_dir = os.path.join(base_dir, ".nexus_cache")
    
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)
        try:
            # 调用系统命令强制将缓存目录设为隐藏，防客户手贱误删
            subprocess.check_call(['attrib', '+H', cache_dir])
        except:
            pass
    return cache_dir

def run_nexus_radar():
    """获客雷达主引擎守护进程"""
    cache_dir = get_safe_cache_dir()
    print(f"[*] 独立浏览器沙盒已挂载: {cache_dir}")
    print("[+] 正在拉起获客引擎，请勿关闭本窗口...")
    
    # 【核心容灾死循环】：防止客户长时间挂机时 Edge 浏览器静默升级导致句柄断开闪退
    while True:
        try:
            # ----------------------------------------------------
            # 这里是你原来的 Playwright / Eel 的核心业务代码
            # 伪代码示例：
            # with sync_playwright() as p:
            #     browser = p.chromium.launch_persistent_context(
            #         user_data_dir=cache_dir,
            #         channel="msedge", # 强制调用系统原生 Edge 防卡死
            #         headless=False
            #     )
            #     page = browser.new_page()
            #     # ... 抓取逻辑 ...
            # ----------------------------------------------------
            
            print("[*] 引擎平稳运行中 (按 Ctrl+C 可强制停止)...")
            time.sleep(3600)  # 模拟长时间运行
            
        except KeyboardInterrupt:
            print("\n[+] 接收到人为退出指令，安全终止。")
            break
        except Exception as e:
            # 捕获一切不可预知的 DOM 崩溃、网络断流或句柄丢失，强制重置但不闪退
            print(f"[!] 检测到内核断连或异常，触发自愈机制重启中... (报错: {str(e)})")
            time.sleep(3)

if __name__ == "__main__":
    # 1. 过卡密
    verify_license()
    # 2. 跑业务
    run_nexus_radar()