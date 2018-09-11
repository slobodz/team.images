# team.images.utils.py
from team.datasync import app_config

def get_column_descriptions():
    STR_SEPARATOR = app_config.STR_SEPARATOR
      
    return 'file_name' + STR_SEPARATOR\
        + 'file_size' + STR_SEPARATOR\
        + 'metadata_image_format' + STR_SEPARATOR\
        + 'metadata_image_width'  + STR_SEPARATOR\
        + 'metadata_image_height' + STR_SEPARATOR\
        + 'metadata_image_dpi' + STR_SEPARATOR\
        + 'product_code_from_file_name' + STR_SEPARATOR\
        + 'possible_product_codes' + STR_SEPARATOR\
        + 'filename_logo_removed' + STR_SEPARATOR\
        + 'filename_is_box_offer' + STR_SEPARATOR\
        + 'filename_is_offer' + STR_SEPARATOR\
        + 'filename_is_label' + STR_SEPARATOR\
        + 'filename_arranged' + STR_SEPARATOR\
        + 'filename_dpi' + STR_SEPARATOR\
        + 'logo_removed' + STR_SEPARATOR\
        + 'filename_image_sequence' + STR_SEPARATOR\
        + 'product_code_from_db' + STR_SEPARATOR\
        + 'new_filename' + STR_SEPARATOR\
        + 'products' + STR_SEPARATOR\
        + 'warnings' + STR_SEPARATOR\
        + 'errors'

def rreplace(given_string, old, new, occurrence):
    split_list = given_string.rsplit(old, occurrence)
    return new.join(split_list)

def list_to_str(lst):
    '''Creates string from string list separated using default separator'''
    list_as_string = ''
    if isinstance(lst, str) is False:
        for iterator in range(0, len(lst)):
            if iterator == 0:
                list_as_string = str(lst[iterator])
            else:
                list_as_string = list_as_string + LIST_SEPARATOR + str(lst[iterator])
    return list_as_string

def exif_str_2_tuple(input_string):
    converted_list = list()
    for char in input_string:
        char2int = ord(char)
        if char2int < 256:
            converted_list.append(char2int)
            converted_list.append(0)
        else:
            converted_list.append(char2int%256)
            converted_list.append(floor(char2int/256))
    converted_list.append(0)
    converted_list.append(0)
    return tuple(converted_list)

def exif_tuple_2_str(input_tuple):
    output_string = ''
    for ix in range(0, len(input_tuple)):
        if ix % 2 == 0:
            lo_byte = input_tuple[ix]
            hi_byte = input_tuple[ix + 1]#this is risky in case tuple has not even number of values
            if lo_byte > 0 or hi_byte > 0:
                output_string = output_string + chr(hi_byte * 256 + lo_byte)
                #ix = ix + 1
    return output_string



