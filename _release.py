import json
import os
import re
import shutil
import subprocess
from datetime import datetime
from sys import exit

from _build import build
from _package import package
from log import logger
from upload_lanzouyun import Uploader
from util import maximize_console
from version import now_version

# 最大化窗口
maximize_console()

# ---------------准备工作
prompt = "如需直接使用默认版本号：{} 请直接按回车\n或手动输入版本号后按回车：".format(now_version)
version = input(prompt) or now_version

version_reg = r"\d+\.\d+\.\d+"

if re.match(version_reg, version) is None:
    logger.info("版本号格式有误，正确的格式类似：1.0.0 ，而不是 {}".format(version))
    exit(-1)

version = 'v' + version

run_start_time = datetime.now()
logger.info("开始发布版本 {}".format(version))

# 先声明一些需要用到的目录的地址
dir_src = os.path.realpath('.')
dir_all_release = os.path.realpath(os.path.join("releases"))
release_dir_name = "DNF蚊子腿小助手_{version}_by风之凌殇".format(version=version)
release_7z_name = '{}.7z'.format(release_dir_name)

# ---------------构建
# 调用构建脚本
os.chdir(dir_src)
build()

# ---------------打包
os.chdir(dir_src)
package(dir_src, dir_all_release, release_dir_name, release_7z_name)

# ---------------复制特定文件到docs目录，用于生成github pages
# logger.info("复制特定文件到docs目录，用于生成github pages")
os.chdir(dir_src)
shutil.copyfile("README.MD", "docs/README.md")
shutil.copyfile("CHANGELOG.MD", "docs/CHANGELOG.md")
subprocess.call(['git', 'add', '--', './docs'])
subprocess.call(['git', 'commit', '-m', '"update github pages"', '--', './docs'])

# ---------------上传到蓝奏云
logger.info("开始上传到蓝奏云")
os.chdir(dir_src)
with open("upload_cookie.json") as fp:
    cookie = json.load(fp)
os.chdir(dir_all_release)
uploader = Uploader(cookie)
if uploader.login_ok:
    logger.info("蓝奏云登录成功，开始上传压缩包")
    uploader.upload_to_lanzouyun(release_7z_name, uploader.folder_djc_helper)
    uploader.upload_to_lanzouyun(release_7z_name, uploader.folder_dnf_calc)
else:
    logger.error("蓝奏云登录失败")

# ---------------推送版本到github
# 打包完成后git添加标签
os.chdir(dir_src)
logger.info("开始推送到github")
# 先尝试移除该tag，并同步到github，避免后面加标签失败
subprocess.call(['git', 'tag', '-d', version])
subprocess.call(['git', 'push', 'origin', 'master', ':refs/tags/{version}'.format(version=version)])
# 然后添加新tab，并同步到github
subprocess.call(['git', 'tag', '-a', version, '-m', 'release {version}'.format(version=version)])
subprocess.call(['git', 'push', 'origin', 'master', '--tags'])

# ---------------结束
logger.info('+' * 40)
logger.info("发布完成，共用时{}，请检查上传至蓝奏云流程是否OK".format(datetime.now() - run_start_time))
logger.info('+' * 40)

os.system("PAUSE")
