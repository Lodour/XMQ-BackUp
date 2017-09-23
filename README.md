# XMQ-BackUp
![](https://img.shields.io/packagist/l/doctrine/orm.svg) ![](https://img.shields.io/badge/python-3.5-ff69b4.svg)

小密圈备份

## Usage
1. 安装 `chromedriver`
> 仅用于登录，如果在浏览器抓包获取了`access_token(authorization)`，则无需安装
  * `brew install chromedriver`
  * 或前往[官网](http://www.seleniumhq.org/download/)/[镜像](http://npm.taobao.org/mirrors/chromedriver/)下载
    * 将包含可执行文件的目录添加至环境变量
    * 或设置`settings.py/CHROME_DRIVER_PATH`为完整执行路径
2. 安装 `XMQ-BackUp`
```bash
git clone git@github.com:Lodour/XMQ-BackUp.git
cd XMQ-BackUp
virtualenv env -p python3.5
source ./env/bin/activate
pip install -r requirements.txt
```

3. 运行
  * 查询 `scrapy list`
  * 运行 `scrapy crawl <spider_name>`
  * 免登陆 `scrapy crawl <spider_name> -a token=<access_token>`

## Note
  * 由于未知原因，使用`phantomjs`渲染所得到的`access_token`不合法，欢迎交流
  * `virtualenv`下使用`scrapy`有问题的请参照[这里](https://segmentfault.com/q/1010000010805727/a-1020000010807816)
