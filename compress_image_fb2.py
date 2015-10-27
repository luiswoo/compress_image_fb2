#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'ipetrash'

"""Скрипт сжимает картинки в файле fb2."""

import os
import base64
import io

from lxml import etree
from PIL import Image


def sizeof_fmt(num, suffix='B'):
    for unit in ['', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Yi', suffix)


# Если True, менять размер изображения
is_resize_image = True

# Использовать процентное изменение размера
use_percent = True

# На сколько процентов изменить размер
percent = 50

# Жестко-заданный размер изображения
set_width, set_height = 350, 500


# TODO: замена в zip архиве
# TODO: сделать как модуль (класс/функция) и консоль


if __name__ == '__main__':
    fb2_file_name = 'mknr_1.fb2'

    total_image_size = 0
    compress_total_image_size = 0

    print(fb2_file_name + ':')

    fb2 = open(fb2_file_name, encoding='utf8')
    xml_fb2 = etree.XML(fb2.read().encode())

    binaries = xml_fb2.xpath("//*[local-name()='binary']")
    for i, binary in enumerate(binaries, 1):
        try:
            content_type = binary.attrib['content-type']
            short_content_type = content_type.split('/')[-1]

            im_id = binary.attrib['id']
            im_data = base64.b64decode(binary.text.encode())
            compress_im_data = im_data

            im = Image.open(io.BytesIO(im_data))
            count_bytes = len(im_data)
            total_image_size += count_bytes

            # Для fb2 доступно 2 формата: png и jpg. jpg в силу своей природы лучше сжат, поэтому
            # способом сжатия может конвертирование в jpg
            if im.format == 'PNG':
                # Конверируем в JPG
                jpeg_buffer = io.BytesIO()
                im.save(jpeg_buffer, format='jpeg')
                compress_im_data = jpeg_buffer.getvalue()

                # Меняем информация о формате и заменяем картинку
                content_type = 'image/jpeg'
                short_content_type = 'jpeg'

            if is_resize_image:
                if use_percent:
                    base_width, base_height = im.size
                    width = int(base_width - (base_width / 100) * percent)
                    height = int(base_height - (base_height / 100) * percent)
                else:
                    width, height = set_width, set_height

                compress_im = Image.open(io.BytesIO(compress_im_data))
                resized_im = compress_im.resize((width, height), Image.ANTIALIAS)

                resize_buffer = io.BytesIO()
                resized_im.save(resize_buffer, format=short_content_type)

                compress_im_data = resize_buffer.getvalue()

            compress_im = Image.open(io.BytesIO(compress_im_data))
            compress_count_bytes = len(compress_im_data)
            compress_total_image_size += compress_count_bytes

            # Меняем информация о формате и заменяем картинку
            binary.attrib['content-type'] = content_type
            binary.text = base64.b64encode(compress_im_data)

            # TODO: показывать только сравнение тех данных, что были изменены
            out_format = ('    {0}. {1}. Compress: {2:.0f}%'
                          '\n        {3} -> {6}'
                          '\n        {4} -> {7}'
                          '\n        {5[0]}x{5[1]} -> {8[0]}x{8[1]}')
            print(out_format.format(i, im_id, 100 - (compress_count_bytes / count_bytes * 100),
                  sizeof_fmt(count_bytes), im.format, im.size,
                  sizeof_fmt(compress_count_bytes), compress_im.format, compress_im.size))

        except Exception as e:
            import traceback
            traceback.print_exc()

    fb2.close()

    fb2_file_size = os.path.getsize(fb2_file_name)
    print()
    print('FB2 file size =', sizeof_fmt(fb2_file_size))
    print('Total image size = {} ({:.0f}%)'.format(sizeof_fmt(total_image_size),
                                                   total_image_size / fb2_file_size * 100))

    if compress_total_image_size:
        compress_fb2_file_name = 'compress_' + fb2_file_name

        # Save to XML file
        tree = etree.ElementTree(xml_fb2)
        tree.write(compress_fb2_file_name, xml_declaration=True, encoding='utf-8')

        print()
        print('Compressed fb2 file saved as {} ({})'.format(compress_fb2_file_name,
                                                            sizeof_fmt(os.path.getsize('compress_' + fb2_file_name))))
        print('Compress total image size = {}'.format(sizeof_fmt(compress_total_image_size)))
        print('Compress: {:.0f}%'.format(100 - (compress_total_image_size / total_image_size * 100)))
    else:
        print('Compress: 0%')
