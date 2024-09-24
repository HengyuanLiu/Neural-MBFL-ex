import seaborn as sns
import matplotlib.pyplot as plt

class GenshinImpactColorPalette:
    class Sumeru:
        Nilou = [
            {"R": 20, "G": 54, "B": 95},
            {"R": 118, "G": 162, "B": 185},
            {"R": 191, "G": 217, "B": 229},
            {"R": 248, "G": 242, "B": 236},
            {"R": 214, "G": 79, "B": 56}
        ]

        Tighnari = [
            {"R": 36, "G": 50, "B": 88},
            {"R": 40, "G": 114, "B": 70},
            {"R": 177, "G": 196, "B": 77},
            {"R": 231, "G": 199, "B": 54},
            {"R": 247, "G": 191, "B": 99},
            {"R": 238, "G": 176, "B": 175},
            {"R": 150, "G": 52, "B": 96},
            {"R": 99, "G": 31, "B": 102},
            {"R": 141, "G": 87, "B": 41},
            {"R": 1, "G": 137, "B": 157}
        ]

        Collei = [
            {"R": 72, "G": 76, "B": 35},
            {"R": 124, "G": 134, "B": 65},
            {"R": 185, "G": 198, "B": 122},
            {"R": 248, "G": 231, "B": 210},
            {"R": 182, "G": 110, "B": 151}
        ]

        Dori = [
            {"R": 112, "G": 89, "B": 146},
            {"R": 169, "G": 115, "B": 153},
            {"R": 214, "G": 130, "B": 148},
            {"R": 243, "G": 191, "B": 202},
            {"R": 41, "G": 31, "B": 39}
        ]

        Faruzan = [
            {"R": 44, "G": 65, "B": 80},
            {"R": 111, "G": 160, "B": 172},
            {"R": 181, "G": 211, "B": 217},
            {"R": 252, "G": 238, "B": 226},
            {"R": 93, "G": 136, "B": 123}
        ]

        Nahida = [
            {"R": 46, "G": 47, "B": 35},
            {"R": 101, "G": 136, "B": 115},
            {"R": 185, "G": 199, "B": 141},
            {"R": 231, "G": 227, "B": 228},
            {"R": 210, "G": 191, "B": 165}
        ]

        Alhaitham = [
            {"R": 25, "G": 49, "B": 52},
            {"R": 54, "G": 104, "B": 107},
            {"R": 76, "G": 164, "B": 162},
            {"R": 175, "G": 176, "B": 171},
            {"R": 136, "G": 116, "B": 87}
        ]

    @classmethod
    def get_palette(cls, character_name, format="normalized"):
        def rgb_to_hex(rgb):
            return '#{:02x}{:02x}{:02x}'.format(rgb[0], rgb[1], rgb[2])
        
        palette = getattr(cls.Sumeru, character_name, None)
        if palette is not None:
            if format == "normalized":
                return [(color['R'] / 255, color['G'] / 255, color['B'] / 255) for color in palette]
            elif format == "hex":
                return [rgb_to_hex((color['R'], color['G'], color['B'])) for color in palette]
            else:
                return palette
        else:
            raise ValueError(f"Character '{character_name}' not found in Sumeru palette.")

    @classmethod
    def show_palette(cls, character_name, title="Color Palette", figsize=None, dpi=None):
        
        palette = cls.get_palette(character_name, format="original")
        
        if figsize is None:
            figsize = (len(palette), 2)
        if dpi is None:
            dpi = len(palette) * 100
        sns_palette = [(color['R'] / 255, color['G'] / 255, color['B'] / 255) for color in palette]
        sns.palplot(sns_palette)
        plt.title(title)
        plt.show()
        
if __name__ == '__main__':
    palette = GenshinImpactColorPalette.get_palette('Nilou')
    print(palette)
