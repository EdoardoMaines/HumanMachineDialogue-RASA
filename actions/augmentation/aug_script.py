import nlpaug.augmenter.char as nac
import nlpaug.augmenter.word as naw
import nlpaug.augmenter.sentence as nas
import nlpaug.flow as nafc
from nlpaug.util import Action

text = "Hello, this is an example and my name is Edoardo!"

aug = nac.KeyboardAug()
augmented_text = aug.augment(text)

print("Original: ", text)
print("Augmented Text: ", augmented_text)