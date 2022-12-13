from log import print_run_msg


def generate_thumbnail(filename):
        # Create thumbnails used on search screens
        # Some images have a 1px border that looks bad in search results
        # Not all do - but we can safely trim 1px off all images
        shave_cmd = "mogrify -shave 1x1 assets/" + filename
        print_run_msg(shave_cmd)
        os.system(shave_cmd)

        # Then we make thumbnails of the border-free images
        create_thumbnail_cmd = "convert -resize x92 assets/" + \
            filename + " assets/50." + filename
        print_run_msg(create_thumbnail_cmd)
        os.system(create_thumbnail_cmd)

def resize_image(filename):
        # Resize images larger than 600x600 down using mogrify from imagemagick
        cmd = "mogrify -resize '600x600>' assets/" + filename
        print_run_msg(cmd)
        os.system(cmd)

def reduce_colour_depth(filename):
        recolor_cmd = "convert -colors 4 assets/" + filename + " assets/" + filename
        print_run_msg(recolor_cmd)
        os.system(recolor_cmd)

def optimise_image(filename):
        optipng_cmd = "optipng -quiet assets/" + filename
        print_run_msg(optipng_cmd)
        os.system(optipng_cmd)

def process_images(pictures_folder):
        for path, dirs, files in os.walk(pictures_folder):
                for filename in files:
                        generate_thumbnail(filename)
                        resize_image(filename)
                        reduce_colour_depth(filename)
                        optimise_image(filename)
