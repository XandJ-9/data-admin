import time

from django.core.management.base import BaseCommand

from apps.datatask.scheduler import TaskSchedulerService


class Command(BaseCommand):
    help = '运行统一任务调度器，支持 cron 扫描与依赖触发'

    def add_arguments(self, parser):
        parser.add_argument('--once', action='store_true', help='只执行一次调度扫描')
        parser.add_argument('--interval', type=int, default=30, help='循环模式下的扫描间隔秒数，默认 30 秒')

    def handle(self, *args, **options):
        run_once = options['once']
        interval = max(options['interval'], 5)

        if run_once:
            summary = TaskSchedulerService.run_cycle()
            self.stdout.write(self.style.SUCCESS(f'调度完成：{summary}'))
            return

        self.stdout.write(self.style.SUCCESS(f'统一任务调度器已启动，扫描间隔 {interval} 秒'))
        try:
            while True:
                summary = TaskSchedulerService.run_cycle()
                self.stdout.write(f'调度完成：{summary}')
                time.sleep(interval)
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING('统一任务调度器已停止'))
