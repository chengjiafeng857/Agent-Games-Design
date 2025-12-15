
import sys
import inspect

try:
    from tencentcloud.ai3d.v20250513 import models
    print("SDK Import Successful")
    
    # Check for ViewImage class/structure
    if hasattr(models, "ViewImage"):
        print("\nFound ViewImage class:")
        view_image = models.ViewImage()
        print(dir(view_image))
        # Print members to see fields
        print(view_image._serialize())
    else:
        print("\nViewImage class NOT found in models")
        
    # Check SubmitHunyuanTo3DProJobRequest to see what parameters it expects
    if hasattr(models, "SubmitHunyuanTo3DProJobRequest"):
        print("\nFound SubmitHunyuanTo3DProJobRequest:")
        req = models.SubmitHunyuanTo3DProJobRequest()
        print(req._serialize())
    else:
        print("\nSubmitHunyuanTo3DProJobRequest NOT found")

except ImportError as e:
    print(f"SDK Import Failed: {e}")
except Exception as e:
    print(f"Error: {e}")
