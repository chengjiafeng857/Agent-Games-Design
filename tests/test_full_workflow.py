"""Comprehensive test for the complete ReAct workflow including asset generation."""

import asyncio
from pathlib import Path
import os
import sys

from agent_games_design.utils.react_cli import SimpleReActCLI
from agent_games_design.state import WorkflowStage, ModelType
from agent_games_design.config import settings


async def test_complete_workflow_with_gemini():
    """Test the complete workflow end-to-end with Gemini 3 Pro asset generation."""
    
    # Skip if no API keys
    if not settings.openai_api_key or settings.openai_api_key == "your-api-key-here":
        print("⚠️  Skipping: OpenAI API key not configured (needed for planning)")
        return
    
    if not settings.gemini_api_key or settings.gemini_api_key == "your-api-key-here":
        print("⚠️  Skipping: Gemini API key not configured (needed for image generation)")
        return
    
    # Create CLI instance
    cli = SimpleReActCLI()
    
    # Simple prompt that should generate 2-3 assets
    prompt = "Design a simple character sprite for a game"
    
    print(f"\n{'='*80}")
    print(f"Testing Complete Workflow: {prompt}")
    print(f"{'='*80}\n")
    
    # Run workflow (non-interactive, auto-approve)
    results = await cli.run_workflow(prompt, interactive=False)
    
    # Verify basic results structure
    assert results is not None, "Results should not be None"
    assert "session_id" in results
    assert "status" in results
    assert "execution_plan" in results
    assert "asset_requests" in results
    assert "generated_assets" in results
    assert "saved_files" in results, "Should have saved_files information"
    
    print(f"\n{'='*80}")
    print("WORKFLOW RESULTS")
    print(f"{'='*80}")
    print(f"Status: {results['status']}")
    print(f"Plan approved: {results.get('plan_approved')}")
    print(f"Execution steps: {len(results['execution_plan'])}")
    print(f"Asset requests: {len(results['asset_requests'])}")
    print(f"Generated assets: {len(results['generated_assets'])}")
    
    # Verify workflow completed
    assert results['status'] in [
        WorkflowStage.COMPLETED.value,
        WorkflowStage.EVALUATION.value
    ], f"Workflow should complete, got: {results['status']}"
    
    # Verify plan was approved
    assert results.get('plan_approved') is True, "Plan should be auto-approved"
    
    # Verify execution plan exists
    assert len(results['execution_plan']) > 0, "Should have execution steps"
    
    # Verify asset requests exist
    assert len(results['asset_requests']) > 0, "Should have asset requests"
    
    print(f"\n{'='*80}")
    print("ASSET REQUESTS")
    print(f"{'='*80}")
    for i, asset_req in enumerate(results['asset_requests'], 1):
        print(f"{i}. {asset_req['title']}")
        print(f"   Type: {asset_req['type']}")
        print(f"   Description: {asset_req.get('description', 'N/A')[:60]}...")
    
    # Verify generated assets
    assert len(results['generated_assets']) > 0, "Should have generated assets"
    
    print(f"\n{'='*80}")
    print("GENERATED ASSETS")
    print(f"{'='*80}")
    
    gemini_assets = []
    successful_assets = []
    
    for i, asset in enumerate(results['generated_assets'], 1):
        status = "✅" if asset.get('image_url') else "❌"
        print(f"{i}. {status} {asset['title']}")
        print(f"   Model: {asset['model_used']}")
        
        # Check for Gemini models (including legacy DALLE_3 and GOOGLE_NANO which now use Gemini)
        if asset['model_used'] in [ModelType.GEMINI_3_PRO.value, ModelType.DALLE_3.value, ModelType.GOOGLE_NANO.value]:
            gemini_assets.append(asset)
        
        if asset.get('image_url'):
            successful_assets.append(asset)
            print(f"   File: {asset['image_url'][:60]}...")
        
        if asset.get('generated_prompt'):
            print(f"   Prompt: {asset['generated_prompt'][:100]}...")
        print()
    
    # Verify Gemini is being used
    print(f"\n{'='*80}")
    print("ASSET GENERATION ANALYSIS")
    print(f"{'='*80}")
    print(f"Total assets: {len(results['generated_assets'])}")
    print(f"Gemini 3 Pro assets: {len(gemini_assets)}")
    print(f"Successful (with images): {len(successful_assets)}")
    
    assert len(gemini_assets) > 0, (
        f"Should have Gemini 3 Pro assets! Got models: "
        f"{[a['model_used'] for a in results['generated_assets']]}"
    )
    
    # Verify successful generation
    assert len(successful_assets) > 0, (
        "Should have at least one successful asset with image_url"
    )
    
    # Verify image files exist (Gemini saves to local files)
    for asset in successful_assets:
        # Gemini saves images locally, so check if path exists
        image_path = Path(asset['image_url'])
        if image_path.exists():
            print(f"✅ Image file exists: {image_path}")
        else:
            # Could be a URL if using a different backend
            assert asset['image_url'].startswith(('http', '/')), (
                f"Image should be a valid path or URL: {asset['image_url']}"
            )
    
    # Verify guidelines were generated
    assert results.get('guidelines'), "Guidelines should be generated"
    assert len(results['guidelines']) > 100, "Guidelines should be substantial"
    
    # Verify saved files
    print(f"\n{'='*80}")
    print("SAVED FILES VERIFICATION")
    print(f"{'='*80}")
    
    saved_files = results['saved_files']
    assert saved_files['folder'], "Should have output folder"
    assert saved_files['markdown'], "Should have markdown file"
    
    from pathlib import Path
    folder = Path(saved_files['folder'])
    markdown = Path(saved_files['markdown'])
    
    print(f"Output folder: {folder}")
    print(f"Markdown file: {markdown.name}")
    
    # Verify folder exists
    assert folder.exists(), f"Output folder should exist: {folder}"
    assert folder.is_dir(), "Output folder should be a directory"
    
    # Verify markdown exists
    assert markdown.exists(), f"Markdown file should exist: {markdown}"
    assert markdown.is_file(), "Markdown should be a file"
    
    # Verify assets folder exists
    assets_folder = folder / "assets"
    assert assets_folder.exists(), "Assets folder should exist"
    assert assets_folder.is_dir(), "Assets folder should be a directory"
    
    # Verify downloaded assets
    if saved_files['assets']:
        print(f"\nDownloaded assets: {len(saved_files['assets'])}")
        for asset_path in saved_files['assets']:
            asset_file = Path(asset_path)
            assert asset_file.exists(), f"Asset file should exist: {asset_file}"
            assert asset_file.is_file(), "Asset should be a file"
            print(f"  ✅ {asset_file.name}")
    
    print(f"\n✅ All saved files verified!")
    
    print(f"\n{'='*80}")
    print("✅ ALL TESTS PASSED!")
    print(f"{'='*80}\n")


async def test_workflow_stages():
    """Test that all workflow stages are executed in the correct order."""
    
    if not settings.openai_api_key or settings.openai_api_key == "your-api-key-here":
        print("⚠️  Skipping: OpenAI API key not configured")
        return
    
    if not settings.gemini_api_key:
        print("⚠️  Skipping: Gemini API key not configured")
        return
    
    cli = SimpleReActCLI()
    prompt = "Create a simple icon"
    
    print(f"\n{'='*80}")
    print("Testing Workflow Stages")
    print(f"{'='*80}\n")
    
    # Start workflow
    state = cli.manager.start_workflow(prompt)
    
    # Track stages
    stages_visited = []
    
    # Execute planning
    print("1. Planning stage...")
    state = cli.manager.execute_step(state)
    stages_visited.append(state.current_stage)
    assert state.current_stage == WorkflowStage.HUMAN_APPROVAL
    print(f"   ✓ Current stage: {state.current_stage.value}")
    
    # Process approval
    print("2. Human approval stage...")
    state = cli.manager.approval_handler.process_human_response(state, "approve")
    assert state.plan_approved is True
    print(f"   ✓ Plan approved")
    
    # Execute ReAct
    print("3. ReAct execution stage...")
    state = cli.manager.execute_step(state)
    stages_visited.append(state.current_stage)
    assert state.current_stage == WorkflowStage.ASSET_GENERATION
    print(f"   ✓ Current stage: {state.current_stage.value}")
    
    # Execute asset generation
    print("4. Asset generation stage...")
    state = cli.manager.execute_step(state)
    stages_visited.append(state.current_stage)
    assert state.current_stage == WorkflowStage.EVALUATION
    print(f"   ✓ Current stage: {state.current_stage.value}")
    print(f"   ✓ Generated {len(state.generated_assets)} assets")
    
    # Execute evaluation
    print("5. Evaluation stage...")
    state = cli.manager.execute_step(state)
    stages_visited.append(state.current_stage)
    assert state.current_stage == WorkflowStage.COMPLETED
    print(f"   ✓ Current stage: {state.current_stage.value}")
    
    print(f"\n{'='*80}")
    print("STAGES VISITED")
    print(f"{'='*80}")
    for i, stage in enumerate(stages_visited, 1):
        print(f"{i}. {stage.value}")
    
    # Verify all expected stages were visited
    expected_stages = [
        WorkflowStage.HUMAN_APPROVAL,
        WorkflowStage.ASSET_GENERATION,
        WorkflowStage.EVALUATION,
        WorkflowStage.COMPLETED
    ]
    
    for expected in expected_stages:
        assert expected in stages_visited, (
            f"Stage {expected.value} should be visited. "
            f"Visited: {[s.value for s in stages_visited]}"
        )
    
    print(f"\n{'='*80}")
    print("✅ ALL STAGE TESTS PASSED!")
    print(f"{'='*80}\n")


async def test_asset_generation_only():
    """Test just the asset generation component."""
    
    if not settings.gemini_api_key:
        print("⚠️  Skipping: Gemini API key not configured")
        return
    
    from agent_games_design.agents import AssetGenerator
    from agent_games_design.state import AssetRequest, AssetType, ModelType
    
    print(f"\n{'='*80}")
    print("Testing Asset Generation (Gemini 3 Pro)")
    print(f"{'='*80}\n")
    
    generator = AssetGenerator()
    
    # Create a simple test request
    request = AssetRequest(
        asset_id="test_001",
        asset_type=AssetType.ICON_SET,
        title="Simple Game Icon",
        description="A simple colorful game icon, 32x32 pixels, vibrant colors",
        style_requirements=["pixel art", "vibrant", "game style"],
        technical_specs={"resolution": "1024x1024", "format": "PNG"},
        reference_images=[],
        target_model=ModelType.GEMINI_3_PRO
    )
    
    print(f"Request: {request.title}")
    print(f"Type: {request.asset_type.value}")
    print(f"Model: {request.target_model.value}")
    print(f"Description: {request.description}\n")
    
    # Generate asset
    print("Generating asset with Gemini 3 Pro...")
    assets = generator.generate_assets([request])
    
    assert len(assets) == 1, "Should generate one asset"
    asset = assets[0]
    
    print(f"\n{'='*80}")
    print("GENERATION RESULT")
    print(f"{'='*80}")
    print(f"Title: {asset.title}")
    print(f"Model: {asset.model_used.value}")
    print(f"Success: {asset.image_url is not None}")
    
    if asset.image_url:
        print(f"Image Path: {asset.image_url}")
        print(f"Quality Score: {asset.quality_score}")
        print(f"Generated Prompt: {asset.generated_prompt[:100]}...")
        
        # Verify image file exists
        image_path = Path(asset.image_url)
        if image_path.exists():
            print(f"Image file size: {image_path.stat().st_size} bytes")
    else:
        print(f"Error: {asset.metadata.get('error', 'Unknown error')}")
    
    # Verify Gemini 3 Pro was used
    assert asset.model_used == ModelType.GEMINI_3_PRO, (
        f"Should use Gemini 3 Pro, got {asset.model_used}"
    )
    
    # Verify image was generated
    assert asset.image_url is not None, "Should have image path"
    
    # Verify image file exists (Gemini saves locally)
    image_path = Path(asset.image_url)
    assert image_path.exists(), f"Image file should exist: {image_path}"
    
    # Verify metadata
    assert asset.metadata is not None, "Should have metadata"
    assert 'timestamp' in asset.metadata, "Should have timestamp"
    assert 'model' in asset.metadata, "Should have model info"
    assert asset.metadata['model'] == 'gemini-3-pro-image-preview', "Should use correct model"
    
    print(f"\n{'='*80}")
    print("✅ ASSET GENERATION TEST PASSED!")
    print(f"{'='*80}\n")


# Legacy alias for backward compatibility
async def test_complete_workflow_with_dalle3():
    """Legacy test name - now uses Gemini 3 Pro."""
    await test_complete_workflow_with_gemini()


if __name__ == "__main__":
    print("\n" + "="*80)
    print(" RUNNING COMPREHENSIVE WORKFLOW TESTS")
    print("="*80 + "\n")
    
    # Check API keys
    if not settings.openai_api_key or settings.openai_api_key == "your-api-key-here":
        print("❌ ERROR: OpenAI API key not configured!")
        print("Please set OPENAI_API_KEY in your .env file")
        exit(1)
    
    if not settings.gemini_api_key:
        print("⚠️  WARNING: Gemini API key not configured!")
        print("Asset generation tests will be skipped.")
        print("Set GEMINI_API_KEY in your .env file for full testing.\n")
    
    # Run tests
    try:
        print("\n1. Testing Complete Workflow...")
        asyncio.run(test_complete_workflow_with_gemini())
        
        print("\n2. Testing Workflow Stages...")
        asyncio.run(test_workflow_stages())
        
        print("\n3. Testing Asset Generation...")
        asyncio.run(test_asset_generation_only())
        
        print("\n" + "="*80)
        print(" ✅ ALL TESTS PASSED! ✅")
        print("="*80 + "\n")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
