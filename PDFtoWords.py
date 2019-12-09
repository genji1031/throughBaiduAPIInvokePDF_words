import json
import requests
import base64
import urllib.parse
import os, logging, traceback
from tkinter.messagebox import *
import tkinter.messagebox
import fitz, re

# 将百度需要调用的api 码 以及 文件名称写入config文件中
API_KEY = ''
SECRECT_KEY = ''
original_picture = ""
original_file_pdf = ""
output_txt = ""

# 原始图片的列表
list_original_picture = []
# 原始图片的名称的列表
list_original_picture_names = []
# 原始文件的列表
list_original_file = []
# 原始文件的名称的列表
list_original_file_names = []

# 设置生成的清晰度，数值越大清晰度越高(默认4.0)
zoom = 4.0
# 设置标头超多少个字就不认为是title了
titles = 25
# 标记该下一行了
flag = 0

# 得到配置文件中的内容
def getConfigContent():
    global API_KEY
    global SECRECT_KEY
    global original_picture
    global output_txt
    global original_file_pdf
    global zoom
    # 打开我们的配置文件将配置信息读取
    with open("config", "rb") as p:
        # 将所有的读取的配置信息进行削减和decode
        API_KEY = p.readline().strip().decode()
        SECRECT_KEY = p.readline().strip().decode()
        original_picture = p.readline().strip().decode()
        original_file_pdf = p.readline().strip().decode()
        output_txt = p.readline().strip().decode()

# 得到图片列表
def getPicList():
    pic = os.listdir(original_picture)
    for i in pic:
        # 将原始图片的地址和名字进行添加
        list_original_picture.append(original_picture+"/"+i)
        list_original_picture_names.append(i)

# 得到pdf 文件 存储名称的列表
def getPDFFileList():
    pdfList = os.listdir(original_file_pdf)
    for i in pdfList:
        # 将原始的PDF列表文件名得到
        list_original_file.append(original_file_pdf+"/"+i)
        list_original_file_names.append(i)

# 使用fitz 去将pdf转图片
def usefitzToPicture():
    for i, n in zip(list_original_file, list_original_file_names):
        doc = fitz.open(i)
        for pg in range(doc.pageCount):
            # pg是每一个pdf页码数字
            print("正在转换图片")
            page = doc[pg]
            rotate = int(0)
            # 设置矩阵  设置清晰度 以及调整角度
            trans = fitz.Matrix(zoom, zoom).preRotate(rotate)
            # create raster image of page (non-transparent)
            pm = page.getPixmap(matrix=trans, alpha=False)
            # 生成图片
            pm.writePNG('{}/{}_{}.png'.format(original_picture, n, pg))
# 文字内容通过百度API得到並根據内容特點進行段落劃分
def executeTranslateContent():
        # invoke
        print("开始执行翻译工作")
        url = 'https://aip.baidubce.com/oauth/2.0/token'
        body = {'grant_type': 'client_credentials',
                'client_id': API_KEY,
                'client_secret': SECRECT_KEY
                }

        req = requests.post(url=url, data=body)
        token = json.loads(req.content)['access_token']

        # baidu translate content
        ocr_url = 'https://aip.baidubce.com/rest/2.0/ocr/v1/general_basic?access_token=%s' % token
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}

        # loop  picture  list  to  find baiduAPI  while invoke we need words！！
        for i, n in zip(list_original_picture, list_original_picture_names):
            # 读取原始图片的地址，得到原始图片流对象
            oo = open(i, 'rb')
            # 写入doc
            w = open(output_txt+"/"+n+".doc", "ab")
            # 将遍历得到的图片读出
            content = oo.read()
            # base64 编码 符合baidu api 的规定
            body = base64.b64encode(content)

            data = urllib.parse.urlencode({'image': body})
            # 请求
            r = requests.post(url=ocr_url, headers=headers, data=data)
            # 得到响应
            res_words = json.loads(r.content)['words_result']
            global titles
            global flag

            # 通過循環來將每次得到的文字内容根據段落特點進行匹配，進行段落劃分的工作
            for words in res_words:

                # 打印输出
                print(words["words"])
                # 如果开头匹配得到（num）那么就说明 很可能是段落开头 需要将走过开头的标记flag设置为1
                if len(re.findall("^\\({0,1}[1-9]+\\)?", words["words"])) != 0 and flag == 0:
                    w.write("\n".encode())
                    w.write("\r".encode())
                    w.write("    ".encode())
                    w.write(words["words"].encode().strip())
                    flag = 1
                # 如果字数比较少且没有句号说明是一个标题开头 需要将走过开头的标记flag设置为1
                elif len(words["words"].strip()) <= titles and "。" not in words["words"] and flag == 0:
                    w.write("\n".encode())
                    w.write("\r".encode())
                    w.write("    ".encode())
                    w.write(words["words"].encode().strip())
                    w.write("\n".encode())
                    w.write("\r".encode())
                    flag = 1
                # 如果句号再最后很可能是段落结尾，需要flag = 1
                elif re.findall("。{1}$", words["words"].strip()) and flag == 0:
                    w.write(words["words"].encode().strip())
                    w.write("\n".encode())
                    w.write("\r".encode())
                    flag = 1
                    # 如果是1-9 加一个符号的可能也是开头段落，或者是大写一二三等 或者是1. 2. 3.
                elif len(re.findall("^[1-9]+、{1}", words["words"].strip())) != 0 or len(re.findall("^\\({0,1}[\u4e00\u4e8c\u4e09\u56db\u4e94\u516d\u4e03\u516b\u4e5d\u5341]?[\u4e00\u4e8c\u4e09\u56db\u4e94\u516d\u4e03\u516b\u4e5d\u5341]{1,3}\\){0,1}、{0,1}", words["words"].strip())) != 0 or len(re.findall("^[1-9]+\\.{1}", words["words"].strip())) != 0:
                    w.write("\n".encode())
                    w.write("\r".encode())
                    w.write("    ".encode())
                    w.write(words["words"].encode().strip())
                # 如果flag为1 说明刚刚走过了一个标题开头， 所以下一段是开头应该加入空行 并且将flag = 0 说明开头段落缩进
                # 已经完成
                elif flag == 1:
                    w.write("\n".encode())
                    w.write("\r".encode())
                    w.write("    ".encode())
                    w.write(words["words"].encode().strip())
                    w.write("\n".encode())
                    w.write("\r".encode())
                    flag = 0
                # 其他情况就追加写入
                else:
                    w.write(words["words"].encode().strip())
            w.close()
            oo.close()


if __name__ == '__main__':
    try:
        # 得到配置信息
        getConfigContent()
        # 得到PDF 文件列表
        getPDFFileList()
        # 使用fitz转PDF TO PICTURE
        usefitzToPicture()
        # 得到图片列表
        getPicList()
        # 执行百度ai翻译
        executeTranslateContent()
        # 画一个提示框
        root = tkinter.Tk()
        root.withdraw()
        d = askokcancel("完成", "已完成")
    except Exception as e:
        # 将异常输出到日记
        log = logging.getLogger("log error")
        fmt = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
        # 确定日记名称
        file_handler = logging.FileHandler("error.txt")
        log.setLevel("DEBUG")
        file_handler.setFormatter(fmt)
        log.addHandler(file_handler)
        # 将堆栈信息输入到log 的 DEBUG 内容中
        log.debug(traceback.format_exc())
        # 画一个提示框 提示错误
        root = tkinter.Tk()
        root.withdraw()
        d = askokcancel("异常", "异常日记已经打印")

