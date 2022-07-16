# Copyright (c) 2022 PaddlePaddle Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from itertools import cycle

import paddlers
from rs_models.test_model import TestModel


class _CDModelAdapter(object):
    def __init__(self, cd_model):
        super().__init__()
        self.cd_model = cd_model

    def __call__(self, input):
        return self.cd_model(input[0], input[1])


class TestCDModel(TestModel):
    EF_MODE = 'None'  # Early-fusion strategy

    def check_output(self, output, target):
        self.assertIsInstance(output, list)
        self.check_output_equal(len(output), len(target))
        for o, t in zip(output, target):
            o = o.numpy()
            self.check_output_equal(o.shape[0], t.shape[0])
            self.check_output_equal(len(o.shape), 4)
            self.check_output_equal(o.shape[2:], t.shape[2:])

    def set_inputs(self):
        if self.EF_MODE == 'Concat':
            # Early-fusion
            def _gen_data(specs):
                for spec in specs:
                    c = spec['in_channels'] // 2
                    assert c * 2 == spec['in_channels']
                    yield [self.get_randn_tensor(c), self.get_randn_tensor(c)]
        elif self.EF_MODE == 'None':
            # Late-fusion
            def _gen_data(specs):
                for spec in specs:
                    c = spec.get('in_channels', 3)
                    yield [self.get_randn_tensor(c), self.get_randn_tensor(c)]
        else:
            raise ValueError
        self.inputs = _gen_data(self.specs)

    def set_targets(self):
        def _gen_data(specs):
            for spec in specs:
                c = spec.get('num_classes', 2)
                yield [self.get_zeros_array(c)]

        self.targets = _gen_data(self.specs)

    def build_model(self, spec):
        model = super().build_model(spec)
        return _CDModelAdapter(model)

    def convert_to_static(self, model, input):
        return super().convert_to_static(model.cd_model, input)


class TestBITModel(TestCDModel):
    MODEL_CLASS = paddlers.custom_models.cd.BIT

    def set_specs(self):
        base_spec = dict(in_channels=3, num_classes=2)
        self.specs = [
            base_spec, 
            dict(**base_spec, backbone='resnet34'), 
            dict(**base_spec, n_stages=3), 
            dict(**base_spec, enc_depth=4, dec_head_dim=16), 
            dict(in_channels=4, num_classes=2), 
            dict(in_channels=3, num_classes=8)
        ]


class TestCDNetModel(TestCDModel):
    MODEL_CLASS = paddlers.custom_models.cd.CDNet
    EF_MODE = 'Concat'

    def set_specs(self):
        self.specs = [
            dict(in_channels=6, num_classes=2), 
            dict(in_channels=8, num_classes=2), 
            dict(in_channels=6, num_classes=8)
        ]


class TestChangeStarModel(TestCDModel):
    MODEL_CLASS = paddlers.custom_models.cd.ChangeStar

    def set_specs(self):
        self.specs = [
            dict(num_classes=2), dict(num_classes=10), 
            dict(num_classes=2, mid_channels=128, num_convs=2), 
            dict(num_classes=2, _phase='eval', _stop_grad=True)
        ]

    def set_targets(self):
        # Avoid allocation of large memories
        tar_c2 = [self.get_zeros_array(2)] * 4
        self.targets = [
            tar_c2,
            [self.get_zeros_array(10)] * 2 + [self.get_zeros_array(2)] * 2,
            tar_c2, [self.get_zeros_array(2)]
        ]


class TestDSAMNetModel(TestCDModel):
    MODEL_CLASS = paddlers.custom_models.cd.DSAMNet

    def set_specs(self):
        base_spec = dict(in_channels=3, num_classes=2)
        self.specs = [
            base_spec, 
            dict(in_channels=8, num_classes=2), 
            dict(in_channels=3, num_classes=8), 
            dict(**base_spec, ca_ratio=4, sa_kernel=5), 
            dict(**base_spec, _phase='eval', _stop_grad=True)
        ]

    def set_targets(self):
        # Avoid allocation of large memories
        tar_c2 = [self.get_zeros_array(2)] * 3
        self.targets = [
            tar_c2, tar_c2, [self.get_zeros_array(8)] * 3, tar_c2,
            [self.get_zeros_array(2)]
        ]


class TestDSIFNModel(TestCDModel):
    MODEL_CLASS = paddlers.custom_models.cd.DSIFN

    def set_specs(self):
        self.specs = [
            dict(num_classes=2), dict(num_classes=10), 
            dict(num_classes=2, use_dropout=True), 
            dict(num_classes=2, _phase='eval', _stop_grad=True)
        ]

    def set_targets(self):
        # Avoid allocation of large memories
        tar_c2 = [self.get_zeros_array(2)] * 5
        self.targets = [
            tar_c2, [self.get_zeros_array(10)] * 5, tar_c2,
            [self.get_zeros_array(2)]
        ]


class TestFCEarlyFusionModel(TestCDModel):
    MODEL_CLASS = paddlers.custom_models.cd.FCEarlyFusion
    EF_MODE = 'Concat'

    def set_specs(self):
        self.specs = [
            dict(in_channels=6, num_classes=2), 
            dict(in_channels=8, num_classes=2), 
            dict(in_channels=6, num_classes=8), 
            dict(in_channels=6, num_classes=2, use_dropout=True)
        ]


class TestFCSiamConcModel(TestCDModel):
    MODEL_CLASS = paddlers.custom_models.cd.FCSiamConc

    def set_specs(self):
        self.specs = [
            dict(in_channels=3, num_classes=2), 
            dict(in_channels=8, num_classes=2), 
            dict(in_channels=3, num_classes=8), 
            dict(in_channels=3, num_classes=2, use_dropout=True)
        ]


class TestFCSiamDiffModel(TestCDModel):
    MODEL_CLASS = paddlers.custom_models.cd.FCSiamDiff

    def set_specs(self):
        self.specs = [
            dict(in_channels=3, num_classes=2), 
            dict(in_channels=8, num_classes=2), 
            dict(in_channels=3, num_classes=8), 
            dict(in_channels=3, num_classes=2, use_dropout=True)
        ]


class TestSNUNetModel(TestCDModel):
    MODEL_CLASS = paddlers.custom_models.cd.SNUNet

    def set_specs(self):
        self.specs = [
            dict(in_channels=3, num_classes=2), 
            dict(in_channels=8, num_classes=2), 
            dict(in_channels=3, num_classes=8), 
            dict(in_channels=3, num_classes=2, width=64)
        ]


class TestSTANetModel(TestCDModel):
    MODEL_CLASS = paddlers.custom_models.cd.STANet

    def set_specs(self):
        base_spec = dict(in_channels=3, num_classes=2)
        self.specs = [
            base_spec, 
            dict(in_channels=8, num_classes=2), 
            dict(in_channels=3, num_classes=8), 
            dict(**base_spec, att_type='PAM'), 
            dict(**base_spec, ds_factor=4)
        ]
