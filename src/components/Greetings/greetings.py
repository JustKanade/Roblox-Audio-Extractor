#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
import random
from PyQt5.QtCore import Qt
from qfluentwidgets import InfoBar, InfoBarPosition, InfoBarIcon

class TimeGreetings:
    """基于时间的问候系统"""
    
    # 中文问候语
    ZH_GREETINGS = {
        'morning': [
            "早上好", "早安", "美好的早晨"
        ],
        'noon': [
            "中午好", "午安", "午餐时间到了"
        ],
        'afternoon': [
            "下午好", "下午安", "愉快的下午"
        ],
        'evening': [
            "晚上好", "晚安", "美好的夜晚"
        ],
        'night': [
            "夜深了", "该休息了", "深夜问候"
        ]
    }
    
    # 中文内容
    ZH_CONTENT_MESSAGES = {
        'morning': [
            "新的一天充满活力，祝您今天愉快！", 
            "早起的鸟儿有虫吃，祝您今天好运！", 
            "早上的阳光真灿烂，愿您的一天也同样美好！"
        ],
        'noon': [
            "是时候休息一下享用午餐了！", 
            "辛苦工作了一上午，记得补充能量哦！", 
            "中午好，记得午休一会儿，下午才有精神！"
        ],
        'afternoon': [
            "下午时光，保持积极的心态！", 
            "下午好，来杯咖啡提提神吧！", 
            "下午时光，加油坚持，马上就能完成今天的任务了！"
        ],
        'evening': [
            "愉快的夜晚时光，放松一下吧！", 
            "晚上好，结束了一天的忙碌，好好犒劳自己吧！", 
            "夜幕降临，是时候放慢脚步，享受宁静时光了！"
        ],
        'night': [
            "已经很晚了，注意休息哦！", 
            "深夜了，工作再重要也要注意身体，早点休息吧！", 
            "夜深了，明天还有新的挑战，早点休息吧！"
        ]
    }
    
    # 英文问候语
    EN_GREETINGS = {
        'morning': [
            "Good Morning", "Morning", "Rise and Shine"
        ],
        'noon': [
            "Good Noon", "Lunch Time", "Midday Greetings"
        ],
        'afternoon': [
            "Good Afternoon", "Afternoon", "Pleasant Afternoon"
        ],
        'evening': [
            "Good Evening", "Evening", "Pleasant Evening"
        ],
        'night': [
            "It's Late", "Time to Rest", "Night Greetings"
        ]
    }
    
    # 英文内容
    EN_CONTENT_MESSAGES = {
        'morning': [
            "A new day full of energy, have a nice day!", 
            "The early bird catches the worm. Good luck today!", 
            "The morning sunshine is bright, may your day be just as wonderful!"
        ],
        'noon': [
            "Time to take a break and enjoy lunch!", 
            "You've worked hard all morning, remember to recharge!", 
            "Good noon, remember to take a break for better afternoon productivity!"
        ],
        'afternoon': [
            "Afternoon time, keep a positive attitude!", 
            "Good afternoon, how about a cup of coffee to refresh?", 
            "Afternoon time, keep going, you're almost done with today's tasks!"
        ],
        'evening': [
            "Pleasant evening time, take a moment to relax!", 
            "Good evening, after a busy day, treat yourself well!", 
            "As night falls, it's time to slow down and enjoy the quiet moments!"
        ],
        'night': [
            "It's getting late, remember to rest!", 
            "Late night, no matter how important work is, take care of your health!", 
            "It's deep into the night, new challenges await tomorrow, get some rest!"
        ]
    }
    
    @staticmethod
    def get_time_period():
        """获取当前时间段"""
        current_hour = datetime.datetime.now().hour
        
        if 5 <= current_hour < 12:
            return 'morning'
        elif 12 <= current_hour < 14:
            return 'noon'
        elif 14 <= current_hour < 18:
            return 'afternoon'
        elif 18 <= current_hour < 22:
            return 'evening'
        else:
            return 'night'
    
    @staticmethod
    def get_greeting(language='zh'):
        """根据当前时间获取适当的问候语
        
        参数:
            language: 语言，'zh'为中文，'en'为英文
        """
        time_period = TimeGreetings.get_time_period()
        
        # 根据语言选择问候语
        if language.lower() == 'en':
            title = random.choice(TimeGreetings.EN_GREETINGS[time_period])
            content = random.choice(TimeGreetings.EN_CONTENT_MESSAGES[time_period])
        else:
            title = random.choice(TimeGreetings.ZH_GREETINGS[time_period])
            content = random.choice(TimeGreetings.ZH_CONTENT_MESSAGES[time_period])
        
        return title, content
    
    @staticmethod
    def show_greeting(language='zh'):
        """显示基于时间的问候桌面通知
        
        参数:
            language: 语言，'zh'为中文，'en'为英文
        """
        try:
            # 获取问候语文本
            title, content = TimeGreetings.get_greeting(language)
            
            # 使用InfoBar显示通知
            # 确保使用正确的参数和设置
            InfoBar.info(
                title=title,
                content=content,
                orient=Qt.Vertical,  # 垂直布局更适合显示问候语
                isClosable=True,     # 允许用户关闭通知
                position=InfoBarPosition.BOTTOM_RIGHT,  # 在右下角显示，不干扰主界面
                duration=5000,       # 显示5秒
                parent=InfoBar.desktopView()  # 使用桌面视图作为父控件
            )
        except Exception as e:
            # 捕获可能的异常，避免问候语显示失败影响主程序
            print(f"显示问候语时出错: {str(e)}") 