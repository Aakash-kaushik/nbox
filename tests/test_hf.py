import os
import unittest

import nbox
from nbox import utils

from functools import cache

@cache
def get_model(*args, **kwargs):
    return nbox.load(*args, **kwargs)

class ImportTest(unittest.TestCase):

    def test_hf_import(self):
        cache_dir = os.path.join(utils.folder(__file__), "__ignore/")
        os.makedirs(cache_dir, exist_ok = True)
        get_model(
            "transformers/sshleifer/tiny-gpt2::AutoModelForCausalLM::generation",
            cache_dir = cache_dir
        )

    def test_hf_string(self):
        cache_dir = os.path.join(utils.folder(__file__), "__ignore/")
        os.makedirs(cache_dir, exist_ok = True)
        model = get_model(
            "transformers/sshleifer/tiny-gpt2::AutoModelForCausalLM::generation",
            cache_dir = cache_dir
        )
        out = model("Hello world")

    def test_hf_numpy(self):
        import numpy as np
        cache_dir = os.path.join(utils.folder(__file__), "__ignore/")
        os.makedirs(cache_dir, exist_ok = True)
        model = get_model(
            "transformers/sshleifer/tiny-gpt2::AutoModelForCausalLM::generation",
            cache_dir = cache_dir
        )
        out = model(np.random.randint(low = 0, high = 100, size = (12,)))

    def test_hf_string_batch(self):
        cache_dir = os.path.join(utils.folder(__file__), "__ignore/")
        os.makedirs(cache_dir, exist_ok = True)
        model = get_model(
            "transformers/sshleifer/tiny-gpt2::AutoModelForCausalLM::generation",
            cache_dir = cache_dir
        )
        out = model(["Hello world", "my foot"])

    # def test_hf_generation(self):
    #     cache_dir = os.path.join(utils.folder(__file__), "__ignore/")
    #     os.makedirs(cache_dir, exist_ok = True)
    #     model = nbox.load(
    #        "transformers/sshleifer/tiny-gpt2::AutoModelForCausalLM::generation",
    #        cache_dir = cache_dir
    #     )
    #     model.generate(...)

    # def test_hf_masked_lm(self):
    #     cache_dir = os.path.join(utils.folder(__file__), "__ignore/")
    #     os.makedirs(cache_dir, exist_ok = True)
    #     model = nbox.load(
    #         "transformers/sshleifer/tiny-gpt2::AutoModelForCausalLM::generation",
    #         cache_dir = cache_dir
    #     )
    #     model.get(...)

if __name__ == '__main__':
    unittest.main()