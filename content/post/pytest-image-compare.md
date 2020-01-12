+++
date = "2020-01-12"
title = "A pytest fixture for image similarity"
slug = "pytest-image"
categories = [ "Post", "Software Development"]
tags = [ "tests", "image", "pytest", "python" ]
+++

When testing codepaths that generate images, one might want to ensure that the generated image is what is expected. [Matplotlib](https://matplotlib.org) has a nice decorator [`@image_comparison`](https://matplotlib.org/devel/testing.html#writing-an-image-comparison-test) that can be applied for this purpose, but looking at [the implementation](https://github.com/matplotlib/matplotlib/blob/f653879c6317b191849c49511282cfff949ad336/lib/matplotlib/testing/decorators.py#L165), it's pretty tied to the `matplotlib` `Figure` object. I wanted something generic to use with PNGs. 

I ended up writing a pytest fixture that would compare the image generated during the test with a baseline image (in `tests/baseline_images` as in the matplotlib implementatino). Here are the contents of `conftest.py`, which contain the fixture and its related image similarity assert:

```py
import os
import pytest
import numpy as np
from PIL import Image


def assert_images_equal(image_1: str, image_2: str):
    img1 = Image.open(image_1)
    img2 = Image.open(image_2)

    # Convert to same mode and size for comparison
    img2 = img2.convert(img1.mode)
    img2 = img2.resize(img1.size)

    sum_sq_diff = np.sum((np.asarray(img1).astype('float') - np.asarray(img2).astype('float'))**2)

    if sum_sq_diff == 0:
        # Images are exactly the same
        pass
    else:
        normalized_sum_sq_diff = sum_sq_diff / np.sqrt(sum_sq_diff)
        assert normalized_sum_sq_diff < 0.001


@pytest.fixture
def image_similarity(request, tmpdir):
    testname = request.node.name
    filename = "{}.png".format(testname)
    generated_file = os.path.join(str(tmpdir), "{}.png".format(testname))

    yield {'filename': generated_file}

    assert_images_equal("tests/baseline_images/{}.png".format(testname), generated_file)
```

The assert rescales the images to be the same size, as well as the same mode, and then computes the sum of the squared differences as an image similarity metric.

You can use the above fixture in a test via:

```py
def test_example(image_similarity):
    # test logic goes here and should generate an image in the
    # path given by image_similarity['filename']
    pass
```

When you add a new test, you need to add the expected image to `tests/baseline_images/<testname>.png`.
