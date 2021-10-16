import time
import requests
import yaml
import math
import random
import os

class TaskError(Exception):
    '''目前(配置/时间/签到情况)不宜完成签到任务'''
    pass

class MT:
    '''MiscTools'''
    @staticmethod
    def geoDistance(lon1, lat1, lon2, lat2):
        '''两经纬度算距离'''
        # 经纬度转换成弧度
        lon1, lat1, lon2, lat2 = map(math.radians, [float(
            lon1), float(lat1), float(lon2), float(lat2)])
        dlon = lon2-lon1
        dlat = lat2-lat1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * \
            math.cos(lat2) * math.sin(dlon/2)**2
        distance = 2*math.asin(math.sqrt(a))*6371393  # 地球平均半径，6371393m
        return distance


class RT:
    '''RandomTools'''
    default_offset = 50
    default_location_round = 6

    @staticmethod
    def locationOffset(lon, lat, offset=default_offset, round_=default_location_round):
        '''经纬度随机偏移(偏移不会累积)
        lon——经度
        lat——纬度
        offset——偏移范围(单位m)
        round_——保留位数
        '''
        # 限定函数(经度-180~180，维度-90~90)

        def limit(n, a, b):
            if n < a:
                n = a
            if n > b:
                n = b
            return n
        # 弧度=弧长/半径，角度=弧长*180°/π，某地经度所对应的圆半径=cos(|维度|)*地球半径
        # ==纬度==
        # 偏移大小
        latOffset = offset/6371393*(180/math.pi)
        # 偏移范围
        lat_a = lat-lat % latOffset
        lat_a = limit(lat_a, -90, 90)
        lat_b = lat+0.99*latOffset-lat % latOffset
        lat_b = limit(lat_b, -90, 90)
        # 随机偏移
        lat = random.uniform(lat_a, lat_b)
        # 保留小数
        lat = round(lat, round_)

        # ==经度==
        # 偏移大小(依赖纬度计算)
        lonOffset = offset / \
            (6371393*math.cos(abs(lat_a/180*math.pi)))*(180/math.pi)
        # 偏移范围
        lon_a = lon-lon % lonOffset
        lon_b = lon+0.99*lonOffset-lon % lonOffset
        lon_a = limit(lon_a, -180, 180)
        lon_b = limit(lon_b, -180, 180)
        # 随机偏移
        lon = random.uniform(lon_a, lon_b)
        # 保留小数
        lon = round(lon, round_)

        return (lon, lat)

    @staticmethod
    def choiceFile(dir):
        '''从指定路径(路径列表)中随机选取一个文件路径'''
        if type(dir) == list:
            dir = random.choice(dir)
        if os.path.isfile(dir):
            return dir
        else:
            files = os.listdir(dir)
            if len(files) == 0:
                raise Exception("路径(%s)指向一个空文件夹" % dir)
            return os.path.join(dir, random.choice(files))

    @staticmethod
    def choiceInList(item):
        if type(item) == list:
            return random.choice(item)
        else:
            return item

    @staticmethod
    def choicePhoto(dir):
        '''从指定路径(路径列表)中随机选取一个图片路径'''
        if type(dir) == list:
            dir = random.choice(dir)
        if os.path.isfile(dir):
            return dir
        else:
            files = filter(lambda x: x.endswith('.jpg'), os.listdir(dir))
            if len(files) == 0:
                raise Exception("路径(%s)指向一个没有图片(.jpg)的文件夹" % dir)
            return os.path.join(dir, random.choice(files))

    @staticmethod
    def randomSleep(a: int, b: int = None):
        '''随机暂停一段时间'''
        if b == None:
            b = a/2
        sleepTime = random.randint(a, b)
        LL.log(0, f'程序正在暂停({sleepTime})')
        time.sleep(sleepTime)


class DT:
    '''DictTools'''
    @staticmethod
    def loadYml(ymlDir='config.yml'):
        with open(ymlDir, 'r', encoding="utf-8") as f:
            return yaml.load(f, Loader=yaml.FullLoader)

    @staticmethod
    def writeYml(item, ymlDir='config.yml'):
        with open(ymlDir, 'w', encoding='utf-8') as f:
            yaml.dump(item, f, allow_unicode=True)

    @staticmethod
    def resJsonEncode(res):
        '''响应内容的json解析函数(换而言之，就是res.json()的小优化版本)'''
        try:
            return res.json()
        except Exception as e:
            raise Exception(
                f'响应内容以json格式解析失败({e})，响应内容:\n\n{res.text}')


class LL:
    '''LiteLog'''
    startTime = time.time()
    log_list = []
    printLevel = 0
    logTypeDisplay = ['debug', 'info', 'warn', 'error', 'critical']

    @staticmethod
    def formatLog(logType: str, args):
        '''返回logItem[时间,类型,内容]'''
        string = ''
        for item in args:
            if type(item) == dict or type(item) == list:
                string += yaml.dump(item, allow_unicode=True)+'\n'
            else:
                string += str(item)+'\n'
        return [time.time()-LL.startTime, logType, string]

    @staticmethod
    def log2FormatStr(logItem):
        logType = LL.logTypeDisplay[logItem[1]]
        return '|||%s|||%0.3fs|||\n%s' % (logType, logItem[0], logItem[2])

    @staticmethod
    def log(logType=1, *args):
        '''日志函数
        logType:int = debug:0|info:1|warn:2|error:3|critical:4'''
        if not args:
            return
        logItem = LL.formatLog(logType, args)
        LL.log_list.append(logItem)
        if logType >= LL.printLevel:
            print(LL.log2FormatStr(logItem))

    @staticmethod
    def getLog(level=0):
        '''获取日志函数'''
        string = ''
        for item in LL.log_list:
            if level <= item[1]:
                string += LL.log2FormatStr(item)
        return string

    @staticmethod
    def saveLog(dir, level=0):
        '''保存日志函数'''
        if type(dir) != str:
            return

        log = LL.getLog(level)
        if not os.path.isdir(dir):
            os.makedirs(dir)
        dir = os.path.join(dir, time.strftime(
            "LOG#t=%Y-%m-%d--%H-%M-%S##.txt", time.localtime()))
        with open(dir, 'w', encoding='utf-8') as f:
            f.write(log)
