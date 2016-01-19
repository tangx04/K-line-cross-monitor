# -*- coding:utf-8 -*-
#凤凰网挂了改用万得数据
import easygui as eg
import time as tm
import numpy as np
import thread
import os
from urllib2 import urlopen, Request
import json
from datetime import datetime, timedelta

URL_IFENG='http://api.finance.ifeng.com/akmin?scode=%s&type=%s'
NUM_PER_THREAD=100#单线程监控的股票数
SCAN_INTERVAL=10
FILE_PATH=u'.\export'
END_HOUR=24
MAX_DATES=100
MSG_HEAD=u'\n 板块   代码        开盘价        均价        收盘价\n'
KDATA_ONE_DAY={'5':48,'15':16,'30':8,'60':4}
K_MIN_LABELS=['5', '15', '30', '60']
cross_list={}

def cross_monitor(codes,ktype,avn,thread_no,retry=3):
         global cross_list
         tmp_codes=[]
         for code in codes:#代码信息改为 [0]证券代码+[1]所属板块+[2]最新行情时间
                  tmp_code=list(code)
                  tmp_code.append(u'0')
                  tmp_codes.append(tmp_code)
         while datetime.now().hour<END_HOUR:
                  start=tm.clock()
                  for code in tmp_codes:
                           for _ in range(retry):
                                    try:
                                             url=URL_IFENG%(code[0],ktype)
                                             request=Request(url)
                                             lines=urlopen(request,timeout=3).read()
                                             js=json.loads(lines)
                                             data=js['record'][-avn:]
                                             if data[-1][0]!=code[2]:
                                                      print u'发现新数据'
                                                      code[2]=data[-1][0]
                                                      mean=0
                                                      for j in range(avn):
                                                               mean=mean+float(data[-(j+1)][3])
                                                      mean=mean/avn
                                                      price_open=float(data[-2][3])
                                                      price_close=float(data[-1][3])
                                                      if price_open<=mean and mean<=price_close:
                                                               cross_list[code[1]][u'cross_codes'].append([code[0][2:8],price_open,mean,price_close])
                                    except Exception as e:
                                             print code,u'数据处理异常，错误信息',e
                                    else:
                                             break
                  finish=tm.clock()
                  print u'线程',thread_no,u'数据获取结束，总耗时',finish-start
                  tm.sleep(20)                  


#弹出提示窗口函数
def showcross():
         global cross_list        
         msg=MSG_HEAD
         for board, lis in cross_list.iteritems():
                  new_num=len(lis[u'cross_codes'])
                  if lis[u'cross_num']<new_num:
                           msg=msg+u'============================================\n'
                           for code in lis[u'cross_codes'][lis[u'cross_num']:new_num]:
                                    msg=msg+'['+board+u'] '+code[0]+'       '+str(code[1])+'       '+str(code[2])+'       '+str(code[3])+'\n'
                           lis[u'cross_num']=new_num
         if msg!=MSG_HEAD:
                  eg.msgbox(msg=msg,title=u'发现K线上穿均线的股票',ok_button=u'知道了')
                  #写日志
                  try:
                           log=open('log.txt','a')
                           log.write('\n'+datetime.now().isoformat(' '))
                           log.write(msg.encode('gbk'))
                  except:
                           eg.msgbox(u'写日志失败')
                  finally:
                           log.close()
         return None
         

if __name__ == "__main__":
         #code=raw_input(u'code:')
         total_codes=0
         avn=0
         codes=[]
         print u'正在启动万得接口，请稍后...'
         ktype=eg.choicebox(msg=u'请选择k线周期', choices=K_MIN_LABELS)
         while(avn<=1):
                  avn=eg.integerbox(msg=u'请输入均线天数，范围在1-500之间', default=10, upperbound=500)
         try:
                  dir_list=os.listdir(FILE_PATH)
         except:
                  eg.msgbox(u'查找数据文件出现异常')
                  exit()
         for dir_name in dir_list:
                  #检查是否为目录
                  path_test=os.path.join(FILE_PATH,dir_name)
                  if os.path.isdir(path_test):
                           cross_list[dir_name]={u'cross_num':0,u'cross_codes':[]}
                           try:
                                    file_list=os.listdir(path_test)
                           except:
                                    eg.msgbox(u'查找数据文件出现异常')
                           for file_name in file_list:
                                    if file_name[0:2]=='SZ':
                                             codes.append([u'sz'+file_name[3:9],dir_name])
                                             total_codes=total_codes+1
                                    elif file_name[0:2]=='SH':
                                             codes.append([u'sh'+file_name[3:9],dir_name])
                                             total_codes=total_codes+1
         if total_codes==0:
                  eg.msgbox(u'没有发现数据文件')
                  exit()
         try:
                  k=0
                  i=0
                  while k<total_codes:
                           if (k+NUM_PER_THREAD)>=total_codes:
                                    thread.start_new_thread(cross_monitor,(codes[k:],ktype,avn,i,))
                           else:
                                    thread.start_new_thread(cross_monitor,(codes[k:k+NUM_PER_THREAD],ktype,avn,i,))
                           i=i+1
                           k=k+NUM_PER_THREAD
         except:
                  eg.msgbox(msg=u'创建监控线程失败')
                  exit()                                    

         while datetime.now().hour<END_HOUR:#下午4点结束监控
                  showcross()
                  tm.sleep(SCAN_INTERVAL)
         eg.msgbox(msg=u'闭市了！')

