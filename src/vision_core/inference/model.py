import torchvision.models as models
import torch.nn as nn
import torch


class VisionCoreModel(nn.Module):
    def __init__(self):
        super().__init__()

        resnet = models.resnet50(
            weights=models.ResNet50_Weights.DEFAULT
        )

        self.backbone = nn.Sequential(
            *list(resnet.children())[:-2]
        )

    def forward(self,x):
        return self.backbone(x)


def load_model(weights_path:str):
    model = VisionCoreModel()

    state_dict = torch.load(
        weights_path,
        map_location='cpu'
    )

    model.load_state_dict(state_dict)

    model.eval()

    return model