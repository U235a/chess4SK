# -*- coding: utf-8 -*-
"""
Created on Wed Aug  6 21:20:28 2025

@author: U235
"""

import os
import cv2
import numpy as np
from tkinter import *
from tkinter import filedialog as fd
from tkinter import messagebox


def change_lines(lines, chess_positions):
    ''' формирование нового списка строк, исходя из словаря позиций диаграмм'''
    flag = False
    file_name = ''
    new_lines = list()
    for line in lines:
        if line[:8] == '[FNAME]=' and (line[8:-1] in chess_positions):
            flag = True
            file_name = line[8:-1]
        if flag and line[:4] == '[B]=':
            lst = line.split(',')
            lst[59] = str(len(chess_positions[file_name]))
            line = ','.join(lst)
            new_lines.append(line)
            x_string = ''.join(
                ['[X]=', ";".join(list(map(str, chess_positions[file_name]))), '\n'])
            x1_string = ''.join(
                ['[X1]=', ','.join(['0' for _ in chess_positions[file_name]]), '\n'])
            new_lines.append(x_string)
            new_lines.append(x1_string)
            flag = False
        else:
            new_lines.append(line)
    return (new_lines)


def filter_coords(coords):
    ''' удаление внутренних прямоугольников, фильтрация координат'''
    n = len(coords)
    inside_rect = []
    for i in range(n):
        for j in range(i+1, n):
            w1 = coords[i][1]-coords[i][0]
            w2 = coords[j][1]-coords[j][0]
            h1 = coords[i][3]-coords[i][2]
            w2 = coords[j][3]-coords[j][2]
            cx1 = 0.5*(coords[i][1]+coords[i][0])
            cx2 = 0.5*(coords[j][1]+coords[j][0])
            cy1 = 0.5*(coords[i][3]+coords[i][2])
            cy2 = 0.5*(coords[j][3]+coords[j][2])
            d = np.sqrt((cx2-cx1)**2+(cy1-cy2)**2)
            if d < 0.4*(w1+w2):
                if w1 > w2:
                    inside_rect.append(j)
                else:
                    inside_rect.append(i)
    return [coords[i] for i in range(n) if i not in inside_rect]


def get_diagramm_pos(tif_name, opts):
    '''поиск положения диаграмм на картинке'''
    # параметры  диаграмм:
    # минимальный размер в долях от высоты страницы 0.093
    min_size_dia = float(opts[1])
    # максимальный размер в долях от высоты страницы 0.2
    max_size_dia = float(opts[2])
    min_aspect_ratio = float(opts[3])  # квадратность 0.96
    expand = int(opts[4])  # отступ от границы диаграммы 5
    # удаление разрывов в диаграммах 5
    dilate_size = (int(opts[5]), int(opts[5]))
    # порядок зон по колонкам, False - по строкам True
    sort_by_colomn = (True, False)[opts[6] == 1]
    img = cv2.imdecode(np.fromfile(tif_name, dtype=np.uint8),
                       cv2.IMREAD_GRAYSCALE)  # если кирилица в путях
    thres = cv2.threshold(
        img, 220, 255, cv2.THRESH_BINARY_INV)[1]

    h, w = thres.shape
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, dilate_size)
    # удаление разрывов в диаграмах, предобработка
    thres = cv2.dilate(thres, kernel)
    num_labels, _, stats, _ = cv2.connectedComponentsWithStats(
        thres, 8, cv2.CV_32S)
    coords = []
    for i in stats:
        if min_size_dia*h < i[3] < max_size_dia*h and \
                min(i[2], i[3])/max(i[2], i[3]) > min_aspect_ratio:
            coord = (i[0]-expand, i[0]+i[2]+expand,  # x1,x2
                     i[1]-expand, i[1]+i[3]+expand)  # y1,y2
            coords.append(coord)
            print(f'{coord}, {i[3]/h:3.3f}')
    coords = filter_coords(coords)  # удаление внутренних прямоугольников
    if sort_by_colomn:
        # сортировка сверху вниз, слева направо
        coords = sorted(coords, key=lambda x: x[0]+0.09*x[2])
    else:
        # сортировка слева направо, сверху вниз
        coords = sorted(coords, key=lambda x: x[2]+0.09*x[0])
    print(coords)
    # имя файла и число найденых на нем диаграмм
    print(tif_name, '\t', len(coords))
    if len(coords) > 0:
        return ({os.path.basename(tif_name): coords})


def get_images_name(lines, page_ranges):
    '''создание списка файлов изображений из spt'''
    filelist = []
    counter = 1
    for line in lines:
        if line[:9] == '[FFNAME]=':
            if (counter in page_ranges) or page_ranges == []:
                filelist.append(line[9:-1])
            counter += 1
    return filelist


def parse_page_ranges(opts):
    '''Парсинг диапазона страниц'''
    pages = []
    segments = opts[7].split(',')
    for segment in segments:
        segment = segment.strip()  # Удаление начальных и конечных пробелов
        if '-' in segment:
            start, end = map(int, segment.split('-'))
            pages.extend(range(start, end + 1))
        elif segment.isdigit():
            pages.append(int(segment))
    return sorted(list(set(pages)))  # Удаление дублей и сортировка


def processing(opts):
    in_name_spt = opts[0]
    chess_positions = dict()
    out_name_spt = ''.join([in_name_spt[:-4], '_new.spt'])
    page_ranges = parse_page_ranges(opts)
    with open(in_name_spt, 'r', encoding='cp1251') as file:
        lines = file.readlines()
    filelist = get_images_name(lines, page_ranges)
    print(filelist[0])
    all_dia_num = 0
    for name in filelist:
        pos = get_diagramm_pos(name, opts)
        if pos is not None:
            all_dia_num += len(list(pos.values())[0])
            chess_positions.update(pos)
    new_lines = change_lines(lines, chess_positions)
    with open(out_name_spt, 'w', encoding='cp1251') as file:
        for line in new_lines:
            file.write(line)
    print('Total diagramms: ', all_dia_num)
    print('*'*7, 'Done', '*'*7)
    messagebox.showinfo(title=None, message='Process completed')


def main():

    root = Tk()
    root.title('Chess4SK   ver.06.08.25')
    root.iconbitmap('chess.ico')

    def get_opts():
        opts = [name_entry.get(), entr_min_size_dia.get(), entr_max_size_dia.get(),
                entr_min_aspect_ratio.get(), entr_expand.get(), entr_dilation.get(),
                c1.get(), pages_entry.get()
                ]
        print('click')
        print(opts)
        processing(opts)

    name = StringVar()
    name_entry = Entry(textvariable=name)

    page_number_rangename = StringVar()
    pages_entry = Entry(textvariable=page_number_rangename)

    def open_dlg():
        global file_path
        file_path = fd.askopenfilename(defaultextension="spt",
                                       filetypes=[("Task file",
                                                   "*.spt"), ("All files", "*.*")], )
        name_entry.delete(0, END)
        name_entry.insert(0, file_path)

        print(file_path)

    label1 = Label(text="min size dia:")
    label2 = Label(text="max size dia:")
    label3 = Label(text="min aspect ratio:")
    label4 = Label(text="expand frame:")
    label5 = Label(text="dilatation dia:")
    label6 = Label(text="page number range:")

    entr_min_size_dia = Spinbox(
        from_=0, to=1.0, format="%.2f", increment=0.01, textvariable=DoubleVar(value=0.09))
    entr_max_size_dia = Spinbox(
        from_=0, to=1.0, format="%.2f", increment=0.01, textvariable=DoubleVar(value=0.25))
    var = DoubleVar(value=0.95)
    entr_min_aspect_ratio = Spinbox(
        from_=0.7, to=1.0, format="%.2f", increment=0.01,  textvariable=var)
    entr_expand = Spinbox(from_=0, to=15, textvariable=IntVar(value=5))
    entr_dilation = Spinbox(from_=0, to=15, textvariable=IntVar(value=5))
    open_button = Button(text="Open spt", command=open_dlg)
    c1 = IntVar(value=0)
    order_by = Checkbutton(root, text="Order by row",
                           variable=c1, onvalue=1, offvalue=0)
    open_button.grid(row=0, column=0, padx=5, pady=5, sticky="w")
    name_entry.grid(row=0, column=1, padx=5, pady=5,
                    sticky=E+W+S+N, columnspan=3)
    label1.grid(row=1, column=0, padx=5, pady=5, sticky="w")
    label2.grid(row=2, column=0, padx=5, pady=5, sticky="w")
    label3.grid(row=1, column=2, padx=5, pady=5, sticky="w")
    label4.grid(row=2, column=2, padx=5, pady=5, sticky="w")
    label5.grid(row=3, column=2, padx=5, pady=5, sticky="w")

    entr_min_size_dia.grid(row=1, column=1, padx=5, pady=5, sticky="w")
    entr_max_size_dia.grid(row=2, column=1, padx=5, pady=5, sticky="w")
    entr_min_aspect_ratio.grid(row=1, column=3, padx=5, pady=5, sticky="w")
    entr_expand.grid(row=2, column=3, padx=5, pady=5, sticky="w")
    entr_dilation.grid(row=3, column=3, padx=5, pady=5, sticky="w")
    order_by.grid(row=3, column=0, padx=5, pady=5, sticky="w")

    label6.grid(row=4, column=0, padx=5, pady=5, sticky="w")
    pages_entry.grid(row=4, column=1, padx=5, pady=5,
                     sticky=E+W+S+N, columnspan=3)

    processing_button = Button(text="Processing", command=get_opts)
    processing_button.grid(row=5, column=1, padx=5,
                           pady=15, sticky=E+W+S+N, columnspan=2)
    root.mainloop()


if __name__ == "__main__":
    main()
