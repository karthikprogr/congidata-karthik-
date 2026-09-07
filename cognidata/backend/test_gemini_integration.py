"""
Test Gemini Integration
Run this to verify your setup is working
"""
import asyncio
import sys
sys.path.insert(0, "d:/Cognidata_mainfinal-main/cognidata/backend")

from app.ai import gemini_flash, gemini_pro, GeminiProvider

async def test_gemini_setup():
    print("=" * 60)
    print("🧪 TESTING GEMINI INTEGRATION")
    print("=" * 60)
    
    # Test 1: List available models
    print("\n📋 Test 1: Listing Available Models...")
    try:
        models = GeminiProvider.list_available_models()
        print(f"✅ Found {len(models)} models")
        print(f"   Using: gemini-3.8-flash (default)")
    except Exception as e:
        print(f"❌ Error: {e}")
        return
    
    # Test 2: Gemini Flash
    print("\n⚡ Test 2: Testing gemini-3.8-flash (fast model)...")
    try:
        response = await gemini_flash.generate_text(
            "Say 'Gemini Flash is working!' in one sentence"
        )
        print(f"✅ Response: {response[:100]}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 3: Gemini Pro  
    print("\n🧠 Test 3: Testing gemini-3.1-pro-preview (complex reasoning)...")
    try:
        response = await gemini_pro.generate_text(
            "Explain AI in exactly 10 words"
        )
        print(f"✅ Response: {response[:100]}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 4: With parameters
    print("\n⚙️  Test 4: Testing with custom parameters...")
    try:
        response = await gemini_flash.generate_text(
            "Count to 5",
            max_tokens=50,
            temperature=0.5
        )
        print(f"✅ Response: {response[:100]}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n" + "=" * 60)
    print("✅ ALL TESTS COMPLETED!")
    print("=" * 60)
    print("\n📄 See GEMINI_INTEGRATION_COMPLETE.md for next steps")
    print("🎯 Next: Update the 5 OpenAI files in your codebase")

if __name__ == "__main__":
    asyncio.run(test_gemini_setup())
