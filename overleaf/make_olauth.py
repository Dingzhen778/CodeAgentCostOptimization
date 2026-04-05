"""
手动创建 .olauth 登录文件
使用方法：
  1. 在浏览器中登录 Overleaf (https://www.overleaf.com)
  2. 按 F12 打开开发者工具 → Application → Cookies → https://www.overleaf.com
  3. 复制 overleaf_session2 和 GCLB 的值
  4. 在 https://www.overleaf.com/project 页面，F12 → Console，执行：
         document.getElementsByName('ol-csrfToken')[0].content
     复制输出的 CSRF token
  5. 将三个值填入下方，运行本脚本
"""

import pickle
import sys

OVERLEAF_SESSION2 = "s%3Aolenj9-A4x96kyWaBwD_oMmsonlpbYtN.zMibA9EKl5GrXSwk9J%2FEXdSjgTfV8TmVe9CLINlp9ok"   # 填入 overleaf_session2 cookie 值
GCLB = "CM-t2JDVoKXofRAD"                # 填入 GCLB cookie 值
CSRF_TOKEN = "sNgngOmx-xZcTkh4yGEy9_Gmd7jw4YElZL1s"          # 填入 CSRF token

OUTPUT_PATH = ".olauth"

if not OVERLEAF_SESSION2 or not GCLB or not CSRF_TOKEN:
    print("请先填写脚本中的三个变量后再运行！")
    sys.exit(1)

store = {
    "cookie": {
        "overleaf_session2": OVERLEAF_SESSION2,
        "GCLB": GCLB,
    },
    "csrf": CSRF_TOKEN,
}

with open(OUTPUT_PATH, "wb") as f:
    pickle.dump(store, f)

print(f"已生成 {OUTPUT_PATH}，可以运行 ols 进行同步了。")
