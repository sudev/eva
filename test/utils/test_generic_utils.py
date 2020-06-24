# coding=utf-8
# Copyright 2018-2020 EVA
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import unittest

from mock import patch

from src.utils.generic_utils import str_to_class, is_gpu_available
from src.loaders.video_loader import VideoLoader


class ModulePathTest(unittest.TestCase):

    def test_should_return_correct_class_for_string(self):
        vl = str_to_class("src.loaders.video_loader.VideoLoader")
        self.assertEqual(vl, VideoLoader)

    @patch('src.utils.generic_utils.torch')
    def test_should_use_torch_to_check_if_gpu_is_available(self,
                                                           torch):
        is_gpu_available()
        torch.cuda.is_available.assert_called()