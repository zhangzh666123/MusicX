from django.apps import AppConfig

class AnalysisConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'analysis'

    def ready(self):
        # 关键：在项目启动时触发单例的初始化
        # 使用 import 延迟加载，避免循环引用
        from .predictor import get_analyzer
        get_analyzer()