#!/usr/bin/env python3
"""
Test script to verify:
1. Haiku verification is working
2. ILRI documents are processed with GROBID
"""

import asyncio
import requests
import json
import os
from pathlib import Path

# API endpoints
API_BASE = "http://localhost:8001"  # ILRI instance
MAIN_API_BASE = "http://localhost:8000"  # Main instance

def test_api_health():
    """Test if ILRI API is running"""
    try:
        response = requests.get(f"{API_BASE}/health", timeout=5)
        print(f"✅ ILRI API Health: {response.status_code}")
        return True
    except Exception as e:
        print(f"❌ ILRI API not accessible: {e}")
        return False

def test_haiku_verification():
    """Test Haiku verification endpoint"""
    test_data = {
        "query": "What are the effects of climate change on agriculture?",
        "answer": "Climate change significantly impacts agriculture through altered precipitation patterns, increased temperatures, and more frequent extreme weather events, leading to reduced crop yields and food security challenges.",
        "context": "Research shows that rising global temperatures and changing rainfall patterns are affecting agricultural productivity worldwide. Drought conditions have increased in many regions, while flooding has become more common in others.",
        "use_haiku": True
    }
    
    try:
        print("\n🧪 Testing Haiku verification...")
        response = requests.post(f"{API_BASE}/query/verify-answer", json=test_data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Haiku verification successful!")
            print(f"   Verification score: {result.get('verification_score', 'N/A')}")
            print(f"   Is supported: {result.get('is_supported', 'N/A')}")
            return True
        else:
            print(f"❌ Haiku verification failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Haiku verification error: {e}")
        return False

def test_openai_verification_comparison():
    """Test OpenAI verification for comparison"""
    test_data = {
        "query": "What are the effects of climate change on agriculture?",
        "answer": "Climate change significantly impacts agriculture through altered precipitation patterns, increased temperatures, and more frequent extreme weather events, leading to reduced crop yields and food security challenges.",
        "context": "Research shows that rising global temperatures and changing rainfall patterns are affecting agricultural productivity worldwide. Drought conditions have increased in many regions, while flooding has become more common in others.",
        "use_haiku": False
    }
    
    try:
        print("\n🧪 Testing OpenAI verification for comparison...")
        response = requests.post(f"{API_BASE}/query/verify-answer", json=test_data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ OpenAI verification successful!")
            print(f"   Verification score: {result.get('verification_score', 'N/A')}")
            print(f"   Is supported: {result.get('is_supported', 'N/A')}")
            return True
        else:
            print(f"❌ OpenAI verification failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ OpenAI verification error: {e}")
        return False

def check_ilri_documents():
    """Check if ILRI documents are in the system"""
    try:
        print("\n📚 Checking for ILRI documents in the system...")
        
        # Try a query that might match ILRI content
        test_query = {
            "query": "livestock health management systems",
            "max_results": 3,
            "use_memory": False
        }
        
        response = requests.post(f"{API_BASE}/query", json=test_query, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            chunks = result.get('chunks', [])
            
            ilri_docs = 0
            grobid_processed = 0
            
            for chunk in chunks:
                source = chunk.get('source', '').lower()
                if 'ilri' in source or any(keyword in source for keyword in ['cgiar', 'livestock', 'animal']):
                    ilri_docs += 1
                    
                # Check if this might have been processed with GROBID
                # (GROBID processed documents typically have better structure)
                text = chunk.get('text', '')
                if len(text.split('.')) > 3 and not text.startswith('\\'):  # Heuristic for structured text
                    grobid_processed += 1
            
            print(f"   Found {len(chunks)} chunks total")
            print(f"   ILRI-related documents: {ilri_docs}")
            print(f"   Likely GROBID-processed: {grobid_processed}")
            
            if ilri_docs > 0:
                print("✅ ILRI documents detected in system")
                return True
            else:
                print("⚠️  No ILRI documents detected - may need ingestion")
                return False
                
        else:
            print(f"❌ Query failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Document check error: {e}")
        return False

def check_grobid_service():
    """Check if GROBID service is running"""
    try:
        print("\n🔬 Checking GROBID service...")
        response = requests.get("http://localhost:8070/api/isalive", timeout=5)
        
        if response.status_code == 200:
            print("✅ GROBID service is running")
            return True
        else:
            print(f"❌ GROBID service not responding: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ GROBID service check failed: {e}")
        return False

def test_query_with_haiku():
    """Test a full query with Haiku verification enabled"""
    test_query = {
        "query": "What are the main challenges in livestock disease prevention?",
        "max_results": 3,
        "use_memory": False,
        "use_amplification": True,
        "use_haiku_verification": True
    }
    
    try:
        print("\n🧪 Testing full query with Haiku verification...")
        response = requests.post(f"{API_BASE}/query", json=test_query, timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Query with Haiku verification successful!")
            print(f"   Answer length: {len(result.get('answer', ''))}")
            print(f"   Verification score: {result.get('verification_score', 'N/A')}")
            print(f"   Subquestions: {len(result.get('subquestions', []))}")
            print(f"   Processing time: {result.get('processing_time', 'N/A'):.2f}s")
            return True
        else:
            print(f"❌ Query with Haiku verification failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Query with Haiku verification error: {e}")
        return False

def main():
    """Run all verification tests"""
    print("🔍 ILRI System Verification Tests")
    print("=" * 50)
    
    results = []
    
    # Test 1: API Health
    results.append(("API Health", test_api_health()))
    
    # Test 2: GROBID Service
    results.append(("GROBID Service", check_grobid_service()))
    
    # Test 3: ILRI Documents
    results.append(("ILRI Documents", check_ilri_documents()))
    
    # Test 4: Haiku Verification
    results.append(("Haiku Verification", test_haiku_verification()))
    
    # Test 5: OpenAI Verification (comparison)
    results.append(("OpenAI Verification", test_openai_verification_comparison()))
    
    # Test 6: Full Query with Haiku
    results.append(("Full Query + Haiku", test_query_with_haiku()))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Summary:")
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All tests passed! System is working correctly.")
    elif passed >= len(results) - 1:
        print("⚠️  Most tests passed. Minor issues detected.")
    else:
        print("🚨 Multiple failures detected. Please check configuration.")

if __name__ == "__main__":
    main()