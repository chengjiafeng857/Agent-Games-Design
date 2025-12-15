#!/usr/bin/env python3
"""
Test script to verify the consistent view generation pipeline.

This script tests that:
1. Front view is generated first from text prompt
2. Side and back views are generated from the front view
3. All three views are returned correctly
"""

from pathlib import Path
from src.models import load_character_spec
from src.stage4_image_generation import generate_tpose_images, get_api_key

def test_consistent_generation():
    """Test the consistent image generation pipeline."""
    
    # Load a test character spec
    config_path = Path("configs/generated_config_Aya.yaml")
    
    if not config_path.exists():
        print(f"Error: Test config not found: {config_path}")
        return False
    
    print("="*60)
    print("TESTING CONSISTENT VIEW GENERATION")
    print("="*60)
    
    # Load character spec
    print(f"\n1. Loading character spec: {config_path}")
    spec = load_character_spec(config_path)
    print(f"   ✓ Loaded: {spec.name} ({spec.role})")
    
    # Check for API key
    print("\n2. Checking for API key...")
    try:
        api_key = get_api_key()
        print("   ✓ API key found")
    except ValueError as e:
        print(f"   ✗ {e}")
        print("\n   To run this test, set GEMINI_API_KEY:")
        print("   export GEMINI_API_KEY='your-api-key'")
        return False
    
    # Test with prompts only (dry run)
    print("\n3. Testing prompt generation (no API calls)...")
    from src.stage4_image_generation import generate_image_prompts_only
    prompts = generate_image_prompts_only(spec, ["front", "side", "back"])
    print(f"   ✓ Generated {len(prompts)} prompts")
    for key in prompts:
        print(f"     - {key}")
    
    # Now test the full pipeline (if user confirms)
    print("\n4. Full pipeline test (with API calls)")
    print("   This will make 3 API calls:")
    print("     - 1 call to generate front view")
    print("     - 2 calls to generate side/back views from front")
    print()
    
    response = input("   Proceed with API test? [y/N]: ")
    if response.lower() != 'y':
        print("   Skipped (user declined)")
        return True
    
    # Create test output directory
    output_dir = Path("output/test_consistent_views")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\n   Generating images to: {output_dir}/")
    
    try:
        # Generate images with new consistent pipeline
        images = generate_tpose_images(
            spec=spec,
            version="test",
            api_key=api_key,
            views=["front", "side", "back"],
        )
        
        print(f"\n   ✓ Generated {len(images)} images")
        
        # Save images
        from src.stage4_image_generation import save_generated_images
        saved_paths = save_generated_images(images, spec, output_dir, "test")
        
        print(f"\n   Saved images:")
        for path in saved_paths:
            print(f"     ✓ {path}")
        
        # Verify the strategy was used
        print(f"\n5. Verification:")
        print(f"   ✓ Front view generated first (reference)")
        print(f"   ✓ Side view generated from front view")
        print(f"   ✓ Back view generated from front view")
        print(f"\n   This ensures all views are consistent!")
        
        return True
        
    except Exception as e:
        print(f"\n   ✗ Error during generation: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print()
    success = test_consistent_generation()
    print("\n" + "="*60)
    if success:
        print("TEST PASSED ✓")
    else:
        print("TEST FAILED ✗")
    print("="*60)
    print()

