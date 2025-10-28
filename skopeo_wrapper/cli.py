#!/usr/bin/env python3
"""
Консольный интерфейс для skopeo-wrapper
"""

import sys
import argparse
import json
from typing import Optional
from .skopeo_wrapper import SkopeoWrapper, create_progress_callback


def main():
    """Основная функция CLI"""
    parser = argparse.ArgumentParser(
        description="Python библиотека-обертка для утилиты skopeo",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  skopeo-wrapper copy docker://alpine:latest dir:/tmp/alpine
  skopeo-wrapper inspect docker://ubuntu:22.04
  skopeo-wrapper copy docker://nginx:latest dir:/tmp/nginx --progress
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Доступные команды')
    
    # Команда copy
    copy_parser = subparsers.add_parser('copy', help='Копирование образа')
    copy_parser.add_argument('source', help='Источник образа')
    copy_parser.add_argument('destination', help='Назначение')
    copy_parser.add_argument('--progress', action='store_true', help='Показать прогресс')
    copy_parser.add_argument('--timeout', type=int, help='Таймаут в секундах')
    
    # Команда inspect
    inspect_parser = subparsers.add_parser('inspect', help='Инспекция образа')
    inspect_parser.add_argument('image', help='URL образа')
    inspect_parser.add_argument('--progress', action='store_true', help='Показать прогресс')
    inspect_parser.add_argument('--timeout', type=int, help='Таймаут в секундах')
    inspect_parser.add_argument('--json', action='store_true', help='Вывести в формате JSON')
    
    # Команда delete
    delete_parser = subparsers.add_parser('delete', help='Удаление образа')
    delete_parser.add_argument('image', help='URL образа')
    delete_parser.add_argument('--progress', action='store_true', help='Показать прогресс')
    delete_parser.add_argument('--timeout', type=int, help='Таймаут в секундах')
    
    # Команда manifest-digest
    digest_parser = subparsers.add_parser('manifest-digest', help='Получение digest манифеста')
    digest_parser.add_argument('image', help='URL образа')
    digest_parser.add_argument('--progress', action='store_true', help='Показать прогресс')
    digest_parser.add_argument('--timeout', type=int, help='Таймаут в секундах')
    
    
    # Общие аргументы
    parser.add_argument('--version', action='version', version='%(prog)s 1.0.0')
    parser.add_argument('--skopeo-path', default='skopeo', help='Путь к исполняемому файлу skopeo')
    parser.add_argument('--enable-metrics', action='store_true', help='Включить сбор метрик')
    parser.add_argument('--disable-metrics', action='store_true', help='Отключить сбор метрик')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Определяем, нужно ли включать метрики
    enable_metrics = True
    if hasattr(args, 'enable_metrics') and getattr(args, 'enable_metrics', False):
        enable_metrics = True
    elif hasattr(args, 'disable_metrics') and getattr(args, 'disable_metrics', False):
        enable_metrics = False
    
    # Создаем экземпляр обертки
    skopeo = SkopeoWrapper(skopeo_path=args.skopeo_path, enable_metrics=enable_metrics)
    
    # Создаем callback для прогресса
    progress_callback = create_progress_callback(show_progress=getattr(args, 'progress', False)) if getattr(args, 'progress', False) else None
    
    try:
        if args.command == 'copy':
            success, stdout, stderr = skopeo.copy(
                source=args.source,
                destination=args.destination,
                progress_callback=progress_callback,
                timeout=getattr(args, 'timeout', None)
            )
            
            if success:
                print("✅ Копирование завершено успешно!")
                sys.exit(0)
            else:
                print(f"❌ Ошибка копирования: {stderr}")
                sys.exit(1)
                
        elif args.command == 'inspect':
            success, stdout, stderr = skopeo.inspect(
                image=args.image,
                progress_callback=progress_callback,
                timeout=getattr(args, 'timeout', None)
            )
            
            if success:
                if args.json:
                    try:
                        data = json.loads(stdout)
                        print(json.dumps(data, indent=2, ensure_ascii=False))
                    except json.JSONDecodeError:
                        print(stdout)
                else:
                    print(stdout)
                sys.exit(0)
            else:
                print(f"❌ Ошибка инспекции: {stderr}")
                sys.exit(1)
                
        elif args.command == 'delete':
            success, stdout, stderr = skopeo.delete(
                image=args.image,
                progress_callback=progress_callback,
                timeout=getattr(args, 'timeout', None)
            )
            
            if success:
                print("✅ Удаление завершено успешно!")
                sys.exit(0)
            else:
                print(f"❌ Ошибка удаления: {stderr}")
                sys.exit(1)
                
        elif args.command == 'manifest-digest':
            success, stdout, stderr = skopeo.get_manifest_digest(
                image=args.image,
                progress_callback=progress_callback,
                timeout=getattr(args, 'timeout', None)
            )
            
            if success:
                print(stdout.strip())
                sys.exit(0)
            else:
                print(f"❌ Ошибка получения digest: {stderr}")
                sys.exit(1)
                
                
    except KeyboardInterrupt:
        print("\n⚠️  Операция прервана пользователем")
        sys.exit(130)
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
