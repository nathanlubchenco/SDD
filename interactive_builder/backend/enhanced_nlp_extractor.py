"""
Enhanced NLP extraction with intelligent entity recognition, context analysis, and semantic understanding
"""

import re
import json
from typing import List, Dict, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from collections import defaultdict
import spacy
from spacy.lang.en import English

@dataclass
class EntityContext:
    """Rich context information for extracted entities"""
    sentence: str
    surrounding_text: str
    position: int
    syntactic_role: str  # subject, object, etc.
    dependencies: List[str]  # related words
    semantic_class: str  # computed semantic category

@dataclass
class EnhancedEntity:
    name: str
    type: str
    canonical_name: str  # normalized form
    description: str
    confidence: float
    context: EntityContext
    relationships: List[str] = field(default_factory=list)
    attributes: Dict[str, Any] = field(default_factory=dict)
    synonyms: Set[str] = field(default_factory=set)

@dataclass
class EntityRelationship:
    """Represents a relationship between entities"""
    source: str
    target: str
    relationship_type: str  # "uses", "contains", "processes", etc.
    confidence: float
    context: str

class EnhancedNLPExtractor:
    """Advanced natural language processing with semantic understanding"""
    
    def __init__(self):
        # Load spaCy model for advanced NLP (fallback to simple if not available)
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            # Fallback to basic English model
            self.nlp = English()
            print("Warning: Advanced spaCy model not available, using basic extraction")
        
        # Enhanced entity patterns with semantic categories
        self.entity_patterns = {
            'actor': {
                'patterns': [
                    r'\b(?:the\s+)?(user|customer|admin|administrator|manager|operator|guest|visitor|member|client|end[\s-]?user|system[\s-]?admin|developer|analyst|stakeholder|owner|reviewer|maintainer|person|individual|team|group|organization)\b',
                ],
                'confidence': 0.9,
                'semantic_indicators': ['PERSON', 'ORG'],
                'context_boost': {
                    'verbs': ['login', 'access', 'create', 'manage', 'view', 'edit', 'delete'],
                    'prepositions': ['for', 'by', 'as']
                }
            },
            'data_entity': {
                'patterns': [
                    r'\b(?:the\s+)?(task|order|product|item|invoice|report|document|file|message|notification|record|entry|transaction|request|response|log|event|session|account|profile|setting|preference|configuration|data|comment|review|rating|feedback|note|attachment|history|output|input|result|analysis|pattern|suggestion|instruction|command|functionality|usage|context|session[\s-]?history|specification|scenario|constraint|entity|relationship|attribute|property|field|value|parameter|variable|object|instance|collection|list|array|table|database|model|schema)\b',
                ],
                'confidence': 0.8,
                'semantic_indicators': ['NOUN'],
                'context_boost': {
                    'verbs': ['store', 'save', 'create', 'update', 'delete', 'process', 'manage'],
                    'adjectives': ['new', 'updated', 'created', 'deleted', 'processed']
                }
            },
            'system_component': {
                'patterns': [
                    r'\b(?:the\s+)?(database|db|server|api|service|application|app|system|platform|interface|ui|frontend|backend|endpoint|microservice|queue|cache|storage|repository|gateway|proxy|load[\s-]?balancer|authentication|auth|authorization|security|encryption|cli|tool|analyzer|parser|processor|generator|extractor|codex[\s-]?cli|claude[\s-]?code|ai[\s-]?tool|framework|library|module|component|service|infrastructure|network|cluster|container|docker|kubernetes|cloud|aws|azure|gcp)\b',
                ],
                'confidence': 0.85,
                'semantic_indicators': ['NOUN', 'PRODUCT'],
                'context_boost': {
                    'verbs': ['deploy', 'run', 'execute', 'host', 'serve', 'provide'],
                    'prepositions': ['on', 'in', 'through', 'via']
                }
            },
            'business_concept': {
                'patterns': [
                    r'\b(?:the\s+)?(workflow|process|procedure|policy|rule|validation|permission|role|access|privilege|scope|domain|category|type|status|state|phase|stage|improvement|optimization|enhancement|recommendation|pattern[\s-]?recognition|analysis|monitoring|tracking|business[\s-]?logic|requirement|constraint|goal|objective|outcome|metric|kpi|sla|compliance|governance|audit|review|approval|workflow|pipeline|lifecycle|journey|experience)\b',
                ],
                'confidence': 0.7,
                'semantic_indicators': ['NOUN'],
                'context_boost': {
                    'verbs': ['define', 'implement', 'follow', 'enforce', 'comply'],
                    'adjectives': ['business', 'organizational', 'operational']
                }
            },
            'action_concept': {
                'patterns': [
                    r'\b(analyze|analyzes|analyzing|analysis|recognize|recognizes|recognizing|recognition|improve|improves|improving|improvement|update|updates|updating|upgrade|generate|generates|generating|creation|process|processes|processing|extract|extracts|extracting|extraction|run|runs|running|execute|execution|create|creates|creating|delete|deletes|deleting|modify|modifies|modifying|transform|transforms|transforming|validate|validates|validating|verify|verifies|verifying|monitor|monitors|monitoring|track|tracks|tracking|manage|manages|managing|configure|configures|configuring|setup|install|deploy|build|compile|test|debug|optimize|refactor|review|approve|submit|cancel|suspend|resume|start|stop|pause|continue|retry|rollback|migrate|backup|restore|sync|integrate|connect|disconnect|join|leave|register|unregister|subscribe|unsubscribe|publish|consume|send|receive|transmit|broadcast|filter|sort|search|query|index|cache|compress|encrypt|decrypt|authenticate|authorize|login|logout|signin|signout|register|enroll|activate|deactivate|enable|disable|lock|unlock|grant|revoke|assign|unassign|allocate|deallocate|reserve|release|acquire|dispose|initialize|finalize|cleanup|refresh|reload|reset|clear|flush|purge|archive|export|import|upload|download|stream|batch|schedule|trigger|invoke|call|request|respond|reply|notify|alert|warn|log|audit|trace|profile|benchmark|measure|calculate|compute|evaluate|assess|estimate|predict|forecast|recommend|suggest|propose|advice|guide|assist|help|support|troubleshoot|diagnose|repair|fix|resolve|handle|catch|throw|raise|emit|dispatch|route|forward|redirect|proxy|balance|distribute|partition|shard|replicate|synchronize|coordinate|orchestrate|choreograph|sequence|order|prioritize|rank|score|rate|weight|normalize|standardize|format|parse|serialize|deserialize|encode|decode|hash|checksum|sign|verify|certify|license|permit|allow|deny|block|filter|sanitize|escape|quote|unquote|trim|pad|split|join|merge|combine|aggregate|group|cluster|classify|categorize|tag|label|annotate|comment|document|describe|explain|clarify|translate|interpret|convert|transform|map|reduce|fold|unfold|flatten|expand|collapse|zoom|pan|rotate|scale|resize|crop|clip|mask|overlay|blend|mix|match|compare|contrast|diff|patch|apply|undo|redo|commit|rollback|branch|merge|rebase|cherry-pick|squash|split|tag|release|publish|deploy|install|uninstall|upgrade|downgrade|migrate|transfer|move|copy|clone|duplicate|backup|restore|recover|salvage|rescue|save|load|persist|store|retrieve|fetch|get|set|put|post|patch|delete|head|options|trace|connect)\b',
                ],
                'confidence': 0.6,
                'semantic_indicators': ['VERB'],
                'context_boost': {
                    'objects': ['data', 'system', 'user', 'process'],
                    'adverbs': ['automatically', 'manually', 'efficiently', 'securely']
                }
            }
        }
        
        # Relationship patterns to identify connections between entities
        self.relationship_patterns = {
            'uses': [
                r'(.+?)\s+(?:uses?|utilizes?|employs?|leverages?)\s+(.+?)(?:\.|,|$)',
                r'(.+?)\s+(?:is\s+)?built\s+(?:on|with|using)\s+(.+?)(?:\.|,|$)',
                r'(.+?)\s+(?:depends\s+on|relies\s+on)\s+(.+?)(?:\.|,|$)'
            ],
            'contains': [
                r'(.+?)\s+(?:contains?|includes?|has|holds)\s+(.+?)(?:\.|,|$)',
                r'(.+?)\s+(?:is\s+)?(?:composed\s+of|made\s+up\s+of)\s+(.+?)(?:\.|,|$)',
                r'(.+?)\s+(?:consists?\s+of)\s+(.+?)(?:\.|,|$)'
            ],
            'processes': [
                r'(.+?)\s+(?:processes?|handles?|manages?|deals\s+with)\s+(.+?)(?:\.|,|$)',
                r'(.+?)\s+(?:is\s+)?(?:responsible\s+for|in\s+charge\s+of)\s+(.+?)(?:\.|,|$)'
            ],
            'communicates_with': [
                r'(.+?)\s+(?:communicates?\s+with|talks\s+to|connects?\s+to|interfaces?\s+with)\s+(.+?)(?:\.|,|$)',
                r'(.+?)\s+(?:sends?\s+(?:data\s+)?to|receives?\s+(?:data\s+)?from)\s+(.+?)(?:\.|,|$)'
            ],
            'creates': [
                r'(.+?)\s+(?:creates?|generates?|produces?|builds?|makes?)\s+(.+?)(?:\.|,|$)',
                r'(.+?)\s+(?:is\s+)?(?:created|generated|produced|built|made)\s+by\s+(.+?)(?:\.|,|$)'
            ]
        }
        
        # Common entity synonyms and variations
        self.entity_synonyms = {
            'user': {'customer', 'client', 'end-user', 'person', 'individual'},
            'admin': {'administrator', 'sys-admin', 'system-admin', 'manager'},
            'api': {'endpoint', 'service', 'interface', 'rest-api', 'web-service'},
            'database': {'db', 'data-store', 'repository', 'storage'},
            'application': {'app', 'software', 'system', 'program'},
            'data': {'information', 'content', 'record', 'entry'},
            'file': {'document', 'attachment', 'resource'},
            'process': {'workflow', 'procedure', 'operation', 'task'},
            'request': {'call', 'query', 'command', 'action'},
            'response': {'reply', 'result', 'output', 'answer'}
        }
        
        # Domain-specific vocabularies
        self.domain_vocabularies = {
            'software_development': {
                'entities': ['repository', 'commit', 'branch', 'merge', 'pull-request', 'issue', 'bug', 'feature', 'release', 'deployment'],
                'actions': ['code', 'debug', 'test', 'deploy', 'refactor', 'review', 'merge', 'commit', 'push', 'pull']
            },
            'web_application': {
                'entities': ['frontend', 'backend', 'middleware', 'router', 'controller', 'model', 'view', 'template', 'session', 'cookie'],
                'actions': ['render', 'route', 'authenticate', 'authorize', 'validate', 'sanitize', 'cache', 'serialize']
            },
            'data_processing': {
                'entities': ['pipeline', 'stream', 'batch', 'job', 'queue', 'worker', 'scheduler', 'transformer', 'aggregator', 'filter'],
                'actions': ['ingest', 'transform', 'aggregate', 'filter', 'enrich', 'normalize', 'deduplicate', 'partition']
            },
            'ai_ml': {
                'entities': ['model', 'dataset', 'feature', 'prediction', 'inference', 'training', 'evaluation', 'metric', 'algorithm', 'pipeline'],
                'actions': ['train', 'predict', 'infer', 'evaluate', 'optimize', 'tune', 'validate', 'cross-validate', 'feature-engineer']
            }
        }

    def extract_entities_enhanced(self, text: str, context: str = "", domain_hint: Optional[str] = None) -> List[EnhancedEntity]:
        """Extract entities with enhanced semantic understanding"""
        # Process text with spaCy for linguistic analysis
        doc = self.nlp(text)
        
        entities = []
        processed_spans = set()  # Track processed text spans to avoid duplicates
        
        # 1. Named Entity Recognition using spaCy
        spacy_entities = self._extract_spacy_entities(doc)
        entities.extend(spacy_entities)
        for entity in spacy_entities:
            processed_spans.add((entity.context.position, entity.context.position + len(entity.name)))
        
        # 2. Pattern-based extraction with syntactic analysis
        pattern_entities = self._extract_pattern_entities(doc, processed_spans, domain_hint)
        entities.extend(pattern_entities)
        
        # 3. Domain-specific extraction
        if domain_hint and domain_hint in self.domain_vocabularies:
            domain_entities = self._extract_domain_entities(doc, domain_hint, processed_spans)
            entities.extend(domain_entities)
        
        # 4. Context-based entity enhancement
        entities = self._enhance_with_context(entities, doc)
        
        # 5. Entity relationship extraction
        relationships = self._extract_relationships(doc, entities)
        entities = self._add_relationships(entities, relationships)
        
        # 6. Entity canonicalization and deduplication
        entities = self._canonicalize_entities(entities)
        
        # 7. Confidence adjustment based on context
        entities = self._adjust_confidence(entities, doc, context)
        
        # Sort by confidence and return top entities
        entities.sort(key=lambda x: x.confidence, reverse=True)
        return entities[:20]  # Limit to top 20 entities
    
    def _extract_spacy_entities(self, doc) -> List[EnhancedEntity]:
        """Extract entities using spaCy's named entity recognition"""
        entities = []
        
        for ent in doc.ents:
            entity_type = self._map_spacy_label_to_type(ent.label_)
            if entity_type:
                context = EntityContext(
                    sentence=ent.sent.text,
                    surrounding_text=self._get_surrounding_text(doc, ent.start, ent.end),
                    position=ent.start_char,
                    syntactic_role=self._get_syntactic_role(ent),
                    dependencies=self._get_dependencies(ent),
                    semantic_class=ent.label_
                )
                
                entities.append(EnhancedEntity(
                    name=ent.text.strip().title(),
                    type=entity_type,
                    canonical_name=self._canonicalize_name(ent.text),
                    description=f"Named entity: {ent.label_} - {ent.text}",
                    confidence=0.85,  # High confidence for spaCy entities
                    context=context
                ))
        
        return entities
    
    def _extract_pattern_entities(self, doc, processed_spans: Set[Tuple[int, int]], domain_hint: Optional[str]) -> List[EnhancedEntity]:
        """Extract entities using enhanced pattern matching with linguistic analysis"""
        entities = []
        text = doc.text
        
        for entity_type, config in self.entity_patterns.items():
            for pattern in config['patterns']:
                for match in re.finditer(pattern, text, re.IGNORECASE):
                    start_char, end_char = match.span()
                    
                    # Skip if already processed
                    if any(start_char < processed_end and end_char > processed_start 
                           for processed_start, processed_end in processed_spans):
                        continue
                    
                    entity_text = match.group(1) if match.groups() else match.group(0)
                    entity_text = entity_text.strip()
                    
                    if len(entity_text) < 2:  # Skip very short entities
                        continue
                    
                    # Find the corresponding spaCy token/span
                    spacy_span = self._find_spacy_span(doc, start_char, end_char)
                    if not spacy_span:
                        continue
                    
                    # Calculate confidence based on context
                    confidence = self._calculate_pattern_confidence(
                        spacy_span, entity_type, config, domain_hint
                    )
                    
                    if confidence < 0.3:  # Skip low-confidence entities
                        continue
                    
                    context = EntityContext(
                        sentence=spacy_span[0].sent.text,
                        surrounding_text=self._get_surrounding_text(doc, spacy_span.start, spacy_span.end),
                        position=start_char,
                        syntactic_role=self._get_syntactic_role(spacy_span),
                        dependencies=self._get_dependencies(spacy_span),
                        semantic_class=self._get_semantic_class(spacy_span)
                    )
                    
                    entities.append(EnhancedEntity(
                        name=entity_text.title(),
                        type=entity_type,
                        canonical_name=self._canonicalize_name(entity_text),
                        description=f"Pattern-based extraction: {entity_text}",
                        confidence=confidence,
                        context=context
                    ))
                    
                    processed_spans.add((start_char, end_char))
        
        return entities
    
    def _extract_domain_entities(self, doc, domain_hint: str, processed_spans: Set[Tuple[int, int]]) -> List[EnhancedEntity]:
        """Extract domain-specific entities"""
        entities = []
        domain_vocab = self.domain_vocabularies.get(domain_hint, {})
        
        # Extract domain-specific entities
        for entity_list in [domain_vocab.get('entities', []), domain_vocab.get('actions', [])]:
            for domain_entity in entity_list:
                pattern = rf'\b{re.escape(domain_entity)}\b'
                for match in re.finditer(pattern, doc.text, re.IGNORECASE):
                    start_char, end_char = match.span()
                    
                    # Skip if already processed
                    if any(start_char < processed_end and end_char > processed_start 
                           for processed_start, processed_end in processed_spans):
                        continue
                    
                    spacy_span = self._find_spacy_span(doc, start_char, end_char)
                    if not spacy_span:
                        continue
                    
                    entity_type = 'action_concept' if domain_entity in domain_vocab.get('actions', []) else 'system_component'
                    
                    context = EntityContext(
                        sentence=spacy_span[0].sent.text,
                        surrounding_text=self._get_surrounding_text(doc, spacy_span.start, spacy_span.end),
                        position=start_char,
                        syntactic_role=self._get_syntactic_role(spacy_span),
                        dependencies=self._get_dependencies(spacy_span),
                        semantic_class=f"domain_{domain_hint}"
                    )
                    
                    entities.append(EnhancedEntity(
                        name=domain_entity.title(),
                        type=entity_type,
                        canonical_name=self._canonicalize_name(domain_entity),
                        description=f"Domain-specific ({domain_hint}): {domain_entity}",
                        confidence=0.75,
                        context=context
                    ))
                    
                    processed_spans.add((start_char, end_char))
        
        return entities
    
    def _extract_relationships(self, doc, entities: List[EnhancedEntity]) -> List[EntityRelationship]:
        """Extract relationships between entities"""
        relationships = []
        text = doc.text
        
        # Create entity name lookup
        entity_names = {entity.canonical_name.lower(): entity.name for entity in entities}
        
        for rel_type, patterns in self.relationship_patterns.items():
            for pattern in patterns:
                for match in re.finditer(pattern, text, re.IGNORECASE):
                    if len(match.groups()) >= 2:
                        source_text = match.group(1).strip()
                        target_text = match.group(2).strip()
                        
                        # Find matching entities
                        source_entity = self._find_matching_entity(source_text, entity_names)
                        target_entity = self._find_matching_entity(target_text, entity_names)
                        
                        if source_entity and target_entity and source_entity != target_entity:
                            relationships.append(EntityRelationship(
                                source=source_entity,
                                target=target_entity,
                                relationship_type=rel_type,
                                confidence=0.7,
                                context=match.group(0)
                            ))
        
        return relationships
    
    def _enhance_with_context(self, entities: List[EnhancedEntity], doc) -> List[EnhancedEntity]:
        """Enhance entities with additional context information"""
        for entity in entities:
            # Add synonyms
            canonical_lower = entity.canonical_name.lower()
            if canonical_lower in self.entity_synonyms:
                entity.synonyms.update(self.entity_synonyms[canonical_lower])
            
            # Add attributes based on context
            entity.attributes = self._extract_entity_attributes(entity, doc)
        
        return entities
    
    def _calculate_pattern_confidence(self, spacy_span, entity_type: str, config: Dict, domain_hint: Optional[str]) -> float:
        """Calculate confidence score for pattern-based entities"""
        base_confidence = config['confidence']
        
        # Boost confidence based on semantic indicators
        semantic_indicators = config.get('semantic_indicators', [])
        if semantic_indicators:
            for token in spacy_span:
                if token.pos_ in semantic_indicators:
                    base_confidence += 0.1
                    break
        
        # Boost confidence based on context
        context_boost = config.get('context_boost', {})
        if context_boost:
            # Check for context verbs
            sent = spacy_span[0].sent
            for token in sent:
                if token.lemma_.lower() in context_boost.get('verbs', []):
                    base_confidence += 0.1
                    break
        
        # Domain relevance boost
        if domain_hint and self._is_domain_relevant(spacy_span.text, domain_hint):
            base_confidence += 0.15
        
        # Syntactic role boost
        syntactic_role = self._get_syntactic_role(spacy_span)
        if syntactic_role in ['nsubj', 'dobj', 'pobj']:  # Important syntactic positions
            base_confidence += 0.05
        
        return min(base_confidence, 0.95)  # Cap at 0.95
    
    def _canonicalize_entities(self, entities: List[EnhancedEntity]) -> List[EnhancedEntity]:
        """Canonicalize and deduplicate entities"""
        canonical_map = {}
        
        for entity in entities:
            canonical = entity.canonical_name.lower()
            
            if canonical in canonical_map:
                # Merge with existing entity, keeping higher confidence
                existing = canonical_map[canonical]
                if entity.confidence > existing.confidence:
                    canonical_map[canonical] = entity
                # Merge synonyms and relationships
                existing.synonyms.update(entity.synonyms)
                existing.relationships.extend(entity.relationships)
            else:
                canonical_map[canonical] = entity
        
        return list(canonical_map.values())
    
    def _adjust_confidence(self, entities: List[EnhancedEntity], doc, context: str) -> List[EnhancedEntity]:
        """Adjust confidence based on global context"""
        for entity in entities:
            # Boost confidence for entities mentioned multiple times
            mentions = len(re.findall(rf'\b{re.escape(entity.canonical_name)}\b', doc.text, re.IGNORECASE))
            if mentions > 1:
                entity.confidence = min(entity.confidence + (mentions - 1) * 0.05, 0.95)
            
            # Boost confidence for entities with relationships
            if entity.relationships:
                entity.confidence = min(entity.confidence + len(entity.relationships) * 0.02, 0.95)
        
        return entities
    
    # Helper methods
    def _map_spacy_label_to_type(self, label: str) -> Optional[str]:
        """Map spaCy entity labels to our entity types"""
        mapping = {
            'PERSON': 'actor',
            'ORG': 'system_component',
            'PRODUCT': 'system_component',
            'EVENT': 'action_concept',
            'WORK_OF_ART': 'data_entity',
            'LAW': 'business_concept',
            'LANGUAGE': 'system_component'
        }
        return mapping.get(label)
    
    def _get_surrounding_text(self, doc, start: int, end: int, window: int = 3) -> str:
        """Get surrounding text context"""
        start_token = max(0, start - window)
        end_token = min(len(doc), end + window)
        return doc[start_token:end_token].text
    
    def _get_syntactic_role(self, span) -> str:
        """Get the syntactic role of a span"""
        if hasattr(span, '__iter__') and len(span) > 0:
            return span[0].dep_
        elif hasattr(span, 'dep_'):
            return span.dep_
        return 'unknown'
    
    def _get_dependencies(self, span) -> List[str]:
        """Get dependency relationships for a span"""
        deps = []
        if hasattr(span, '__iter__'):
            for token in span:
                deps.extend([child.text for child in token.children])
        elif hasattr(span, 'children'):
            deps = [child.text for child in span.children]
        return deps
    
    def _get_semantic_class(self, span) -> str:
        """Get semantic classification for a span"""
        if hasattr(span, '__iter__') and len(span) > 0:
            return span[0].pos_
        elif hasattr(span, 'pos_'):
            return span.pos_
        return 'unknown'
    
    def _find_spacy_span(self, doc, start_char: int, end_char: int):
        """Find spaCy span corresponding to character positions"""
        try:
            return doc.char_span(start_char, end_char)
        except:
            return None
    
    def _canonicalize_name(self, name: str) -> str:
        """Canonicalize entity name"""
        return re.sub(r'[^\w\s-]', '', name.lower().strip()).replace(' ', '_')
    
    def _find_matching_entity(self, text: str, entity_names: Dict[str, str]) -> Optional[str]:
        """Find matching entity for relationship extraction"""
        text_lower = text.lower().strip()
        
        # Direct match
        if text_lower in entity_names:
            return entity_names[text_lower]
        
        # Partial match
        for canonical, name in entity_names.items():
            if canonical in text_lower or text_lower in canonical:
                return name
        
        return None
    
    def _extract_entity_attributes(self, entity: EnhancedEntity, doc) -> Dict[str, Any]:
        """Extract attributes for an entity from context"""
        attributes = {}
        
        # Extract common attributes based on entity type
        if entity.type == 'actor':
            attributes['permissions'] = self._extract_permissions(entity, doc)
            attributes['roles'] = self._extract_roles(entity, doc)
        elif entity.type == 'data_entity':
            attributes['properties'] = self._extract_properties(entity, doc)
            attributes['operations'] = self._extract_operations(entity, doc)
        elif entity.type == 'system_component':
            attributes['technologies'] = self._extract_technologies(entity, doc)
            attributes['interfaces'] = self._extract_interfaces(entity, doc)
        
        return attributes
    
    def _extract_permissions(self, entity: EnhancedEntity, doc) -> List[str]:
        """Extract permissions for actor entities"""
        permissions = []
        # Implementation would look for permission patterns near the entity
        return permissions
    
    def _extract_roles(self, entity: EnhancedEntity, doc) -> List[str]:
        """Extract roles for actor entities"""
        roles = []
        # Implementation would look for role patterns near the entity
        return roles
    
    def _extract_properties(self, entity: EnhancedEntity, doc) -> List[str]:
        """Extract properties for data entities"""
        properties = []
        # Implementation would look for property patterns near the entity
        return properties
    
    def _extract_operations(self, entity: EnhancedEntity, doc) -> List[str]:
        """Extract operations for data entities"""
        operations = []
        # Implementation would look for operation patterns near the entity
        return operations
    
    def _extract_technologies(self, entity: EnhancedEntity, doc) -> List[str]:
        """Extract technologies for system components"""
        technologies = []
        # Implementation would look for technology patterns near the entity
        return technologies
    
    def _extract_interfaces(self, entity: EnhancedEntity, doc) -> List[str]:
        """Extract interfaces for system components"""
        interfaces = []
        # Implementation would look for interface patterns near the entity
        return interfaces
    
    def _is_domain_relevant(self, text: str, domain_hint: str) -> bool:
        """Check if text is relevant to the domain"""
        if domain_hint not in self.domain_vocabularies:
            return False
        
        domain_vocab = self.domain_vocabularies[domain_hint]
        all_terms = domain_vocab.get('entities', []) + domain_vocab.get('actions', [])
        
        text_lower = text.lower()
        return any(term.lower() in text_lower for term in all_terms)
    
    def _add_relationships(self, entities: List[EnhancedEntity], relationships: List[EntityRelationship]) -> List[EnhancedEntity]:
        """Add relationship information to entities"""
        entity_map = {entity.name: entity for entity in entities}
        
        for rel in relationships:
            if rel.source in entity_map:
                entity_map[rel.source].relationships.append(f"{rel.relationship_type}:{rel.target}")
            if rel.target in entity_map:
                entity_map[rel.target].relationships.append(f"inverse_{rel.relationship_type}:{rel.source}")
        
        return entities

    def detect_domain(self, text: str) -> Optional[str]:
        """Detect the most likely domain for the text"""
        text_lower = text.lower()
        domain_scores = {}
        
        for domain, vocab in self.domain_vocabularies.items():
            score = 0
            all_terms = vocab.get('entities', []) + vocab.get('actions', [])
            
            for term in all_terms:
                if term.lower() in text_lower:
                    score += 1
            
            if score > 0:
                domain_scores[domain] = score / len(all_terms)  # Normalize by vocabulary size
        
        if domain_scores:
            return max(domain_scores, key=domain_scores.get)
        
        return None