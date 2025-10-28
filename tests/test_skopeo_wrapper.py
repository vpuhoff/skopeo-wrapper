#!/usr/bin/env python3
"""
Тесты для skopeo_wrapper
"""

import pytest
import os
import tempfile
import subprocess
from skopeo_wrapper import SkopeoWrapper, create_progress_callback, ProgressInfo


@pytest.fixture
def skopeo_wrapper():
    """Фикстура для создания экземпляра SkopeoWrapper"""
    return SkopeoWrapper()


@pytest.fixture
def temp_dir():
    """Фикстура для создания временной директории"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


def test_skopeo_available():
    """Тест доступности skopeo"""
    try:
        result = subprocess.run(['skopeo', '--version'], 
                              capture_output=True, text=True, check=True)
        assert "skopeo version" in result.stdout
    except (subprocess.CalledProcessError, FileNotFoundError):
        pytest.skip("Skopeo не установлен")


def test_skopeo_wrapper_creation(skopeo_wrapper):
    """Тест создания экземпляра SkopeoWrapper"""
    assert skopeo_wrapper is not None
    assert skopeo_wrapper.skopeo_path == "skopeo"


def test_skopeo_wrapper_custom_path():
    """Тест создания SkopeoWrapper с кастомным путем"""
    wrapper = SkopeoWrapper(skopeo_path="/custom/path/skopeo")
    assert wrapper.skopeo_path == "/custom/path/skopeo"


def test_inspect_image(skopeo_wrapper):
    """Тест инспекции образа"""
    success, stdout, stderr = skopeo_wrapper.inspect(
        image="docker://docker.io/library/alpine:latest"
    )
    
    assert success
    assert "Architecture" in stdout
    assert "Os" in stdout


def test_copy_image(skopeo_wrapper, temp_dir):
    """Тест копирования образа"""
    destination = f"dir:{temp_dir}/alpine"
    
    success, stdout, stderr = skopeo_wrapper.copy(
        source="docker://docker.io/library/alpine:latest",
        destination=destination
    )
    
    assert success
    assert os.path.exists(f"{temp_dir}/alpine")
    assert os.path.exists(f"{temp_dir}/alpine/manifest.json")


def test_copy_with_progress(skopeo_wrapper, temp_dir):
    """Тест копирования с прогрессом"""
    destination = f"dir:{temp_dir}/ubuntu"
    progress_callback = create_progress_callback(show_progress=True)
    
    success, stdout, stderr = skopeo_wrapper.copy(
        source="docker://docker.io/library/ubuntu:22.04",
        destination=destination,
        progress_callback=progress_callback
    )
    
    assert success
    assert os.path.exists(f"{temp_dir}/ubuntu")


def test_error_handling(skopeo_wrapper):
    """Тест обработки ошибок"""
    success, stdout, stderr = skopeo_wrapper.copy(
        source="docker://docker.io/library/nonexistent:latest",
        destination="dir:/tmp/nonexistent"
    )
    
    # Проверяем, что операция не удалась
    assert not success, f"Expected operation to fail, but success={success}"
    
    # Для несуществующих образов skopeo может не возвращать текст ошибки
    # но success должен быть False


def test_progress_info_creation():
    """Тест создания ProgressInfo"""
    progress = ProgressInfo(
        operation="copy",
        current_step="copying_blob",
        current_blob=None,
        manifest_written=False,
        signatures_stored=False,
        error=None,
        completed=False
    )
    
    assert progress.operation == "copy"
    assert progress.current_step == "copying_blob"
    assert not progress.completed


def test_create_progress_callback():
    """Тест создания callback для прогресса"""
    callback = create_progress_callback(show_progress=True)
    assert callback is not None
    assert callable(callback)


if __name__ == "__main__":
    pytest.main([__file__])
