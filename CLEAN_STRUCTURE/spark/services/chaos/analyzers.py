#!/usr/bin/env python3
"""
EdenOS MCP Server Hub - CHAOS Analyzers
Analyzes CHAOS file components for insights.
"""

from typing import Dict, Any, List

class ChaosAnalyzers:
    """Analyzes CHAOS file components for insights."""
    
    def analyze_emotions(self, emotions: List[Dict]) -> Dict[str, Any]:
        """Analyze emotions from CHAOS file."""
        if not emotions:
            return {"emotion_count": 0, "emotion_types": [], "intensity_distribution": {}, "dominant_emotion": None, "emotional_intensity_score": 0}

        intensity_counts = {"EXTREME": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "MINIMAL": 0}
        emotion_types = []

        for emotion in emotions:
            emotion_types.append(emotion["type"])
            if emotion["intensity"] in intensity_counts:
                intensity_counts[emotion["intensity"]] += 1

        dominant_emotion = None
        if emotion_types:
            for emotion in emotions:
                if emotion["intensity"] == "EXTREME":
                    dominant_emotion = emotion["type"]
                    break
            if not dominant_emotion:
                for emotion in emotions:
                    if emotion["intensity"] == "HIGH":
                        dominant_emotion = emotion["type"]
                        break
            if not dominant_emotion and emotions:
                dominant_emotion = emotions[0]["type"]

        intensity_score = 0
        intensity_weights = {"EXTREME": 10, "HIGH": 7, "MEDIUM": 5, "LOW": 3, "MINIMAL": 1}
        for emotion in emotions:
            if emotion["intensity"] in intensity_weights:
                intensity_score += intensity_weights[emotion["intensity"]]
        if emotions:
            intensity_score = min(100, (intensity_score / (len(emotions) * 10)) * 100)

        return {
            "emotion_count": len(emotions),
            "emotion_types": emotion_types,
            "intensity_distribution": intensity_counts,
            "dominant_emotion": dominant_emotion,
            "emotional_intensity_score": intensity_score
        }
    
    def analyze_symbols(self, symbols: List[Dict]) -> Dict[str, Any]:
        """Analyze symbols from CHAOS file."""
        if not symbols:
            return {"symbol_count": 0, "symbol_types": [], "presence_distribution": {}, "dominant_symbol": None}

        presence_counts = {"STRONG": 0, "PRESENT": 0, "WEAK": 0}
        symbol_types = []

        for symbol in symbols:
            symbol_types.append(symbol["type"])
            if symbol["presence"] in presence_counts:
                presence_counts[symbol["presence"]] += 1

        dominant_symbol = None
        if symbol_types:
            for symbol in symbols:
                if symbol["presence"] == "STRONG":
                    dominant_symbol = symbol["type"]
                    break
            if not dominant_symbol and symbols:
                dominant_symbol = symbols[0]["type"]

        return {
            "symbol_count": len(symbols),
            "symbol_types": symbol_types,
            "presence_distribution": presence_counts,
            "dominant_symbol": dominant_symbol
        }
    
    def analyze_relationships(self, relationships: List[Dict]) -> Dict[str, Any]:
        """Analyze relationships from CHAOS file."""
        if not relationships:
            return {"relationship_count": 0, "entities": [], "relationship_types": [], "graph": {}}

        entities = set()
        relationship_types = set()

        for rel in relationships:
            entities.add(rel["source"])
            entities.add(rel["target"])
            relationship_types.add(rel["type"])

        graph = {}
        for entity in entities:
            graph[entity] = {"outgoing": [], "incoming": []}

        for rel in relationships:
            source = rel["source"]
            target = rel["target"]
            rel_type = rel["type"]

            graph[source]["outgoing"].append({
                "target": target,
                "type": rel_type
            })
            graph[target]["incoming"].append({
                "source": source,
                "type": rel_type
            })

        return {
            "relationship_count": len(relationships),
            "entities": list(entities),
            "relationship_types": list(relationship_types),
            "graph": graph
        }
    
    def analyze_chaosfield(self, chaosfield_content: str) -> Dict[str, Any]:
        """Analyze chaosfield content from CHAOS file."""
        if not chaosfield_content:
            return {"word_count": 0, "line_count": 0, "character_count": 0, "themes": []}

        lines = [line.strip() for line in chaosfield_content.split('\n') if line.strip()]
        words = chaosfield_content.split()
        
        # Simple theme detection (could be enhanced with NLP)
        common_themes = ["eden", "chaos", "order", "creation", "destruction", "life", "death", "love", "hate", "fire", "water", "earth", "air"]
        found_themes = []
        
        content_lower = chaosfield_content.lower()
        for theme in common_themes:
            if theme in content_lower:
                found_themes.append(theme)

        return {
            "word_count": len(words),
            "line_count": len(lines),
            "character_count": len(chaosfield_content),
            "themes": found_themes
        }
    
    def analyze_composition(self, parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze overall composition of CHAOS file."""
        emotive_layer = parsed_data.get("emotive_layer", {})
        chaosfield_layer = parsed_data.get("chaosfield_layer", "")
        
        emotion_count = len(emotive_layer.get("emotions", []))
        symbol_count = len(emotive_layer.get("symbols", []))
        relationship_count = len(emotive_layer.get("relationships", []))
        
        chaosfield_analysis = self.analyze_chaosfield(chaosfield_layer)
        
        # Calculate complexity score
        complexity_score = (
            emotion_count * 2 +
            symbol_count * 1.5 +
            relationship_count * 3 +
            min(chaosfield_analysis["word_count"] / 100, 10)
        )
        
        # Determine balance
        total_elements = emotion_count + symbol_count + relationship_count
        if total_elements == 0:
            balance = "empty"
        elif emotion_count > symbol_count and emotion_count > relationship_count:
            balance = "emotion_dominant"
        elif symbol_count > emotion_count and symbol_count > relationship_count:
            balance = "symbol_dominant"
        elif relationship_count > emotion_count and relationship_count > symbol_count:
            balance = "relationship_dominant"
        else:
            balance = "balanced"
        
        return {
            "complexity_score": min(100, complexity_score),
            "balance_type": balance,
            "element_counts": {
                "emotions": emotion_count,
                "symbols": symbol_count,
                "relationships": relationship_count
            },
            "chaosfield_metrics": chaosfield_analysis
        }
    
    def compare_files(self, file1_data: Dict[str, Any], file2_data: Dict[str, Any]) -> Dict[str, Any]:
        """Compare two CHAOS files for similarities and differences."""
        parsed1 = file1_data.get("parsed", {})
        parsed2 = file2_data.get("parsed", {})
        
        # Compare emotions
        emotions1 = {e["type"]: e["intensity"] for e in parsed1.get("emotive_layer", {}).get("emotions", [])}
        emotions2 = {e["type"]: e["intensity"] for e in parsed2.get("emotive_layer", {}).get("emotions", [])}
        
        common_emotions = set(emotions1.keys()) & set(emotions2.keys())
        unique_emotions_1 = set(emotions1.keys()) - set(emotions2.keys())
        unique_emotions_2 = set(emotions2.keys()) - set(emotions1.keys())
        
        # Compare symbols
        symbols1 = {s["type"]: s["presence"] for s in parsed1.get("emotive_layer", {}).get("symbols", [])}
        symbols2 = {s["type"]: s["presence"] for s in parsed2.get("emotive_layer", {}).get("symbols", [])}
        
        common_symbols = set(symbols1.keys()) & set(symbols2.keys())
        unique_symbols_1 = set(symbols1.keys()) - set(symbols2.keys())
        unique_symbols_2 = set(symbols2.keys()) - set(symbols1.keys())
        
        # Calculate similarity score
        total_elements = len(emotions1) + len(emotions2) + len(symbols1) + len(symbols2)
        common_elements = len(common_emotions) + len(common_symbols)
        similarity_score = (common_elements * 2 / total_elements * 100) if total_elements > 0 else 0
        
        return {
            "similarity_score": min(100, similarity_score),
            "emotions": {
                "common": list(common_emotions),
                "unique_to_file1": list(unique_emotions_1),
                "unique_to_file2": list(unique_emotions_2)
            },
            "symbols": {
                "common": list(common_symbols),
                "unique_to_file1": list(unique_symbols_1),
                "unique_to_file2": list(unique_symbols_2)
            }
        }
