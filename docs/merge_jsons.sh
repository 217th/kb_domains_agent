#!/bin/bash

# --- НАСТРОЙКИ ---
# Получаем текущую дату и время.
# Формат: YYYYMMDDHHMM (например, 202511221430)
TIMESTAMP=$(date +"%Y%m%d%H%M")
OUTPUT_FILE="combined_jsons_${TIMESTAMP}.txt"
SEPARATOR="--------------------------------------------------------------------------------"

# Очищаем (или создаем) выходной файл перед началом
> "$OUTPUT_FILE"

# Проверяем, есть ли json файлы в директории
if ! ls *.json 1> /dev/null 2>&1; then
    echo "Файлы .json не найдены в текущей директории."
    exit 1
fi

# --- 1. ГЕНЕРАЦИЯ ОГЛАВЛЕНИЯ ---
echo "=== ОГЛАВЛЕНИЕ / TABLE OF CONTENTS ===" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"
ls -1 *.json >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"
echo "$SEPARATOR" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

# --- 2. СКЛЕЙКА ФАЙЛОВ ---
for file in *.json; do
    # Записываем имя файла
    echo "FILE: $file" >> "$OUTPUT_FILE"
    
    # Пустая строка
    echo "" >> "$OUTPUT_FILE"
    
    # Содержимое файла (без изменений)
    cat "$file" >> "$OUTPUT_FILE"
    
    # Пустая строка после содержимого
    echo "" >> "$OUTPUT_FILE"
    
    # Разделитель
    echo "$SEPARATOR" >> "$OUTPUT_FILE"
    
    # Пустая строка перед следующим блоком
    echo "" >> "$OUTPUT_FILE"
done

echo "Готово! Результат сохранен в файл: $OUTPUT_FILE"
