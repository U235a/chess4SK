# chess4SK
Add chess diagrams from scans to ScanKromsator task-file.

chess4SK.py - скрипт поиска шахматных диаграмм на сканированных страницах.
Порядок работы:
1. Открыть ScanKromsator (проверено на SK v.6.71), добавить изображения, отметить все зелеными галками (отмаркировать все файлы). 
Сохранить файл-задание .spt (важно: зоны и резаки не расставлять!!!) Закрыть SK.
2. Запустить chess4SK.py, в интерфейсе выбрать нужный spt-файл, расставить опции, если необходимо, и нажать кнопку Process. Создасться новый spt файл, там же где у вас находится изначальный spt файл.
5. Запустить SK, открыть этот новый spt, после открытия надо заменить тип зон Bulk operations... на Picture-zone.

![screenshot](https://github.com/U235a/chess4SK/blob/main/screenshot.png "screenshot")
