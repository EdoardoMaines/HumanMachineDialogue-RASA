from typing import Dict, Text, Any, List
from rasa.engine.graph import GraphComponent, ExecutionContext
from rasa.engine.recipes.default_recipe import DefaultV1Recipe
from rasa.engine.storage.resource import Resource
from rasa.engine.storage.storage import ModelStorage
from rasa.shared.nlu.training_data.message import Message
from rasa.shared.nlu.training_data.training_data import TrainingData

from spellchecker import SpellChecker
from fuzzywuzzy import process

import re


@DefaultV1Recipe.register(
    [DefaultV1Recipe.ComponentType.MESSAGE_FEATURIZER], is_trainable=False
)
class CustomNLUComponent(GraphComponent):
    def __init__(
        self,
        config: Dict[Text, Any],
        model_storage: ModelStorage,
        resource: Resource,
        execution_context: ExecutionContext
    ) -> None:
        self.config = config
        self.spell = SpellChecker()
        self.all_entities =  ["baby", "medium", "large", "small",  "margherita", "marinara", "salami", "veggie", "mozzarella", "mushrooms", "ham", 
                                  "spicy salami", "olives", "vegetables", "grilled vegetables", "coke", "still water", "sparkling water",
                                  "fanta", "lemon tea", "peach tea", "tomato sauce", "pizza dough"]
        self.available_type_entity = ["pizza_type", "pizza_size", "pizza_topping", "drink", "ingredient"]
        self.entity_dict = {
            "pizza_type": ["margherita", "marinara", "salami", "veggie"],
            "pizza_size": ["baby", "medium", "large", "small"],
            "pizza_topping": ["mozzarella", "mushrooms", "ham", "spicy salami", "olives", "vegetables", "grilled vegetables"],
            "drink": ["coke", "still water", "sparkling water", "fanta", "lemon tea", "peach tea"],
            "id": ["test identity", "testidentity", "edward identity", "edwardidentity"],
            "password": ["test password", "testpassword", "edward password", "edwardpassword"],
            "ingredient": ["tomato sauce", "pizza dough"]
        }
        self.model_storage = model_storage
        self.resource = resource
        self.execution_context = execution_context

    @classmethod
    def create(
        cls,
        config: Dict[Text, Any],
        model_storage: ModelStorage,
        resource: Resource,
        execution_context: ExecutionContext,
    ) -> GraphComponent:
        
        return cls(config, model_storage, resource, execution_context)

    def train(self, training_data: TrainingData) -> Resource:
        pass

    def process_training_data(self, training_data: TrainingData) -> TrainingData:
        return training_data

    def process(self, messages: List[Message]) -> List[Message]:
        messages = self.correct_spelling(messages)
        return messages
    
    def correct_spelling(self, messages: List[Message]) -> List[Message]:
        
        for message in messages:
            
            entities = message.get("entities", [])
            text_message = message.get("text")
            if entities:

                domain_words = self.all_entities

                new_entities = []
                
                for entity in entities:
                    entity_text = entity.get("value", "")
                    type = entity.get("entity")
                    confidence = entity.get("confidence_entity")

                    if type in self.available_type_entity or confidence <= 0.5:
                        if entity_text not in domain_words:
                            old_entity_start = entity.get("start")
                            
                            new_entity_value = None

                            if entity_text:
                                corrected_text, score = self.get_best_match(entity_text, domain_words)

                                if corrected_text in self.all_entities and score >= 80:
                                    new_entity_start = old_entity_start
                                    new_entity_end = new_entity_start + len(corrected_text)
                                    
                                    entity['entity'] = self.get_entity_name(corrected_text)
                                    entity['value'] = corrected_text
                                    entity['start'] = new_entity_start
                                    entity['end'] = new_entity_end
                                    entity['confidence_entity'] = 0.9
                                    temp_entity = self.check_and_add_entity(new_entities, entity)
                                    if temp_entity != None:
                                        new_entities.append(entity)
                                        new_entity_value = corrected_text
                                        new_message_text = self.replace_word_in_text(text_message, entity_text, new_entity_value)
                                        text_message = new_message_text
                                    else:
                                        text_message = self.remove_word_in_text(text_message, entity_text)
                            else:
                                new_entities.append(entity)
                                new_entity_value = corrected_text
                        else:
                            new_entities.append(entity)
                    else:
                        new_entities.append(entity)

                new_entities = self.remove_duplicate_entities(new_entities)
                new_entities = self.correct_entities_indices(new_entities, text_message)
                message.set("entities", new_entities)
                message.set("text", text_message)            

        return messages

    def get_best_match(self, word: Text, domain_words: List[Text]) -> Text:
        self.spell.word_frequency.load_words(domain_words)
        corrected_word = self.spell.correction(word)
        if not corrected_word:
            score = 0
            return word, score
        best_match, score = process.extractOne(corrected_word, domain_words)
        
        if score:
            return best_match, score
        return word, score

    def get_entity_name (self, word: Text) -> Text:
        for category, items in self.entity_dict.items():
            if word in items:
                return category
        return None

    def replace_word_in_text(self, text: str, old_word: str, new_word: str) -> str:
        pattern = r'\b{}\b'.format(re.escape(old_word))
        replaced_text = re.sub(pattern, new_word, text)
        return replaced_text
    
    def remove_word_in_text(text: str, word_to_remove: str) -> str:
        pattern = r'\b{}\b'.format(re.escape(word_to_remove))
        
        if not re.search(pattern, text):
            return text
        
        modified_text = re.sub(pattern, '', text)
        modified_text = re.sub(r'\s+', ' ', modified_text).strip()
        return modified_text
    
    def remove_duplicate_entities(self, entities):
        seen_entities = set()
        unique_entities = []

        for entity in entities:
            value = entity.get("value")
            start = entity.get("start")
            end = entity.get("end")
            
            entity_tuple = (value, start, end)
            
            if entity_tuple not in seen_entities:
                seen_entities.add(entity_tuple)
                unique_entities.append(entity)

        return unique_entities
    
    def check_and_add_entity(self, entities, new_entity):
        new_value = new_entity.get("value")
        new_start = new_entity.get("start")
        new_end = new_entity.get("end")
        
        for entity in entities:
            if entity.get("value") == new_value:
                if entity.get("start") == new_start and entity.get("end") == new_end:
                    return None
                
        return new_entity
    
    def correct_entities_indices(self, entities, text):
        corrected_entities = []

        for entity in entities:
            value = entity['value']
            original_start = entity['start']
            original_end = entity['end']
            
            possible_starts = [i for i in range(len(text)) if text.startswith(value, i)]
            
            correct_start = None
            for start in possible_starts:
                if start == original_start:
                    correct_start = start
                    break

            if correct_start is None:
                corrected_entities.append(entity)
                continue
            
            correct_end = correct_start + len(value)
            
            if correct_start != original_start or correct_end != original_end:
                corrected_entity = entity.copy()
                corrected_entity['start'] = correct_start
                corrected_entity['end'] = correct_end
                corrected_entities.append(corrected_entity)
            else:
                corrected_entities.append(entity)
        
        return corrected_entities
