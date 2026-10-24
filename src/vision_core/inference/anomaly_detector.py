import torch
import torch.nn.functional as f

def load_anomaly_detector(path:str):
    checkpoint = torch.load(
        path,
        map_location="cpu",
        weights_only=False
    )

    memory_banks = checkpoint['memory_banks']
    thresholds = checkpoint['thresholds']
    supported_categories = checkpoint['supported_categories']

    return memory_banks,thresholds,supported_categories

def feature_map_to_patches(features):
    batch_size,channels,height,width = features.shape

    features = features.permute(
        0,2,3,1
    )

    features = features.reshape(
        batch_size,
        height * width,
        channels
    )

    return features



def nearest_distance(test_patch : torch.Tensor , memory_bank : torch.Tensor):
    test_patch = f.normalize(
        test_patch,
        p=2,
        dim=0
    )

    similarity = torch.matmul(
        memory_bank,
        test_patch
    )

    distance = 1 - similarity

    return distance.min()


def calculate_patch_distances(test_patch : torch.Tensor , memory_bank : torch.Tensor):
    distances = torch.cdist(
        test_patch,
        memory_bank,
        p=2
    )

    min_distances = distances.min(dim=1).values

    return min_distances


def predict_anomaly(model,image,memory_bank, device):
    model.eval()

    image = image.unsqueeze(0).to(device)

    with torch.inference_mode():
        features = model(image)

        patches = feature_map_to_patches(features)

        patches = patches.squeeze(0)

        patch_distance = calculate_patch_distances(
            patches,
            memory_bank
        )

        top_k = 10

        top_k_distance = torch.topk(
            patch_distance,
            top_k
        ).values

        anomaly_score = top_k_distance.mean()

        return anomaly_score


def detect_anomaly(model,memory_banks,thresholds,category,image,device):
    memory_bank = memory_banks[category]
    threshold = thresholds[category]

    anomaly_score = predict_anomaly(
        model,
        image,
        memory_bank,
        device
    )


    if anomaly_score > threshold:
        prediction = "anomaly"
    else:
        prediction = "normal"

    return prediction, anomaly_score