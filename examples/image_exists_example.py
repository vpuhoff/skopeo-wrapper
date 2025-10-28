#!/usr/bin/env python3
"""
Примеры использования функции проверки существования образов
"""

import json
from skopeo_wrapper import SkopeoWrapper, create_progress_callback


def example_basic_image_check():
    """Базовый пример проверки существования образов"""
    print("🔍 Базовый пример проверки существования образов")
    print("=" * 60)
    
    # Создаем экземпляр обертки
    skopeo = SkopeoWrapper()
    
    # Список образов для проверки
    images = [
        "docker://docker.io/library/alpine:latest",
        "docker://docker.io/library/ubuntu:22.04",
        "docker://docker.io/library/nonexistent:latest",
        "docker://docker.io/library/nginx:alpine"
    ]
    
    print("\n📋 Проверка существования образов:")
    
    for image in images:
        print(f"\n🔍 Проверка {image}...")
        
        success, exists, error_msg = skopeo.image_exists(
            image=image,
            progress_callback=create_progress_callback(show_progress=True)
        )
        
        if success:
            if exists:
                print(f"   ✅ Образ существует")
            else:
                print(f"   ❌ Образ не найден")
        else:
            print(f"   ⚠️  Ошибка проверки: {error_msg}")


def example_detailed_image_check():
    """Детальный пример с анализом результатов"""
    print("\n🔍 Детальный пример проверки образов")
    print("=" * 60)
    
    skopeo = SkopeoWrapper(enable_metrics=True)
    
    # Тестируем различные типы образов
    test_cases = [
        {
            "image": "docker://docker.io/library/alpine:latest",
            "description": "Популярный образ Alpine Linux"
        },
        {
            "image": "docker://docker.io/library/ubuntu:22.04",
            "description": "Образ Ubuntu 22.04"
        },
        {
            "image": "docker://docker.io/library/nonexistent:latest",
            "description": "Несуществующий образ"
        },
        {
            "image": "docker://docker.io/library/redis:alpine",
            "description": "Образ Redis на Alpine"
        }
    ]
    
    results = []
    
    for test_case in test_cases:
        image = test_case["image"]
        description = test_case["description"]
        
        print(f"\n📦 {description}")
        print(f"   Образ: {image}")
        
        success, exists, error_msg = skopeo.image_exists(image=image)
        
        result = {
            "image": image,
            "description": description,
            "success": success,
            "exists": exists,
            "error": error_msg
        }
        results.append(result)
        
        if success:
            if exists:
                print(f"   ✅ Статус: Образ существует")
            else:
                print(f"   ❌ Статус: Образ не найден")
        else:
            print(f"   ⚠️  Статус: Ошибка - {error_msg}")
    
    # Выводим сводку результатов
    print(f"\n📊 Сводка результатов:")
    print(f"   Всего проверено: {len(results)}")
    print(f"   Существуют: {sum(1 for r in results if r['success'] and r['exists'])}")
    print(f"   Не найдены: {sum(1 for r in results if r['success'] and not r['exists'])}")
    print(f"   Ошибки: {sum(1 for r in results if not r['success'])}")
    
    return results


def example_json_output():
    """Пример с выводом результатов в JSON формате"""
    print("\n🔍 Пример с JSON выводом")
    print("=" * 60)
    
    skopeo = SkopeoWrapper(enable_metrics=True)
    
    images = [
        "docker://docker.io/library/alpine:latest",
        "docker://docker.io/library/ubuntu:22.04",
        "docker://docker.io/library/nonexistent:latest"
    ]
    
    results = []
    
    for image in images:
        success, exists, error_msg = skopeo.image_exists(image=image)
        
        result = {
            "image": image,
            "exists": exists,
            "success": success,
            "error": error_msg
        }
        results.append(result)
    
    print("\n📄 Результаты в JSON формате:")
    print(json.dumps(results, indent=2, ensure_ascii=False))


def example_conditional_operations():
    """Пример условных операций на основе проверки существования"""
    print("\n🔍 Пример условных операций")
    print("=" * 60)
    
    skopeo = SkopeoWrapper(enable_metrics=True)
    
    source_image = "docker://docker.io/library/alpine:latest"
    target_image = "docker://docker.io/library/alpine:backup"
    
    print(f"📦 Исходный образ: {source_image}")
    print(f"📦 Целевой образ: {target_image}")
    
    # Проверяем существование исходного образа
    print(f"\n🔍 Проверка исходного образа...")
    success, source_exists, error_msg = skopeo.image_exists(source_image)
    
    if not success:
        print(f"❌ Ошибка проверки исходного образа: {error_msg}")
        return
    
    if not source_exists:
        print(f"❌ Исходный образ не существует, операция невозможна")
        return
    
    print(f"✅ Исходный образ существует")
    
    # Проверяем существование целевого образа
    print(f"\n🔍 Проверка целевого образа...")
    success, target_exists, error_msg = skopeo.image_exists(target_image)
    
    if not success:
        print(f"❌ Ошибка проверки целевого образа: {error_msg}")
        return
    
    if target_exists:
        print(f"⚠️  Целевой образ уже существует, пропускаем копирование")
    else:
        print(f"✅ Целевой образ не существует, можно копировать")
        print(f"📦 Выполняем копирование...")
        
        # Здесь можно было бы выполнить копирование
        # success, stdout, stderr = skopeo.copy(source_image, target_image)
        print(f"   (Копирование пропущено в примере)")


def main():
    """Основная функция с примерами"""
    print("🚀 Примеры использования функции проверки существования образов")
    print("=" * 80)
    
    try:
        # Базовый пример
        example_basic_image_check()
        
        # Детальный пример
        example_detailed_image_check()
        
        # JSON вывод
        example_json_output()
        
        # Условные операции
        example_conditional_operations()
        
        print("\n" + "=" * 80)
        print("🏁 Все примеры завершены!")
        print("\n💡 Дополнительные возможности:")
        print("   - CLI команда: skopeo-wrapper image-exists <image>")
        print("   - JSON вывод: skopeo-wrapper image-exists <image> --json")
        print("   - С прогрессом: skopeo-wrapper image-exists <image> --progress")
        
    except Exception as e:
        print(f"❌ Ошибка выполнения примеров: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()