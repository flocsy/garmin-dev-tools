import Toybox.Lang;
import Toybox.Graphics;
import Toybox.System;
import Toybox.WatchUi;

// hash

(:datafield, :datafield_hash, :inline)
function datafield_hash(width as Number, height as Number, obscurityFlags as DataField.Obscurity) as Number {
  return (width * 1000 + height) * 100 + obscurityFlags;
}

// label

(:datafield, :datafield_hash, :datafield_label_font, :no_hebrew, :inline)
function datafield_label_font(hash as Number) as Graphics.FontDefinition? {
  var dict = DATAFIELD_HASH_2_LABEL_FONT;
  return dict.hasKey(hash) ? dict[hash] as Graphics.FontDefinition? : DEFAULT_LABEL_FONT;
}
(:no_ciq_3_1_0, :datafield, :datafield_hash, :datafield_label_font, :hebrew, :inline)
function datafield_label_font(hash as Number) as Graphics.FontDefinition? {
  var dict = DATAFIELD_HASH_2_LABEL_FONT;
  return dict.hasKey(hash) ? dict[hash] as Graphics.FontDefinition? : DEFAULT_LABEL_FONT;
}
(:ciq_3_1_0, :datafield, :datafield_hash, :datafield_label_font, :no_ttf_font, :hebrew, :inline)
function datafield_label_font(hash as Number) as Graphics.FontDefinition? {
  var dict = DATAFIELD_HASH_2_LABEL_FONT;
  var increment = INCREASE_HEBREW_LABEL_FONT_SIZE && System.getDeviceSettings().systemLanguage /*api 3.1.0*/ == System.LANGUAGE_HEB ? 1 : 0;
  var font = dict.hasKey(hash) ? dict[hash] : DEFAULT_LABEL_FONT;
  return (font == null || font instanceof Lang.Boolean ? null : font as Number + increment) as Graphics.FontDefinition?;
}
(:ciq_3_1_0, :datafield, :datafield_hash, :datafield_label_font, :ttf_font, :hebrew, :inline)
function datafield_label_font(hash as Number) as Graphics.FontType? {
  var dict = DATAFIELD_HASH_2_LABEL_FONT;
  var font = dict.hasKey(hash) ? dict[hash] : DEFAULT_LABEL_FONT;
  if (font instanceof Lang.Symbol) {
    font = Graphics.getVectorFont(TTF_FONTS[font] as VectorFontOptions);
  } else {
    var increment = INCREASE_HEBREW_LABEL_FONT_SIZE && System.getDeviceSettings().systemLanguage /*api 3.1.0*/ == System.LANGUAGE_HEB ? 1 : 0;
    font = (font == null || font instanceof Lang.Boolean ? null : font as Number + increment) as Graphics.FontDefinition?;
  }
  return font;
}

(:datafield, :datafield_hash, :datafield_label_x, :inline)
function datafield_label_x(hash as Number) as Number? {
  var dict = DATAFIELD_HASH_2_LABEL_X;
  // return dict.hasKey(hash) ? dict[hash] as Number : DEFAULT_LABEL_X;
  var label_x = dict.hasKey(hash) ? dict[hash] : DEFAULT_LABEL_X;
  return (label_x == null || label_x instanceof Lang.Boolean ? null : label_x) as Number?;
}

(:datafield, :datafield_hash, :datafield_label_y, :inline)
function datafield_label_y(hash as Number) as Number? {
  var dict = DATAFIELD_HASH_2_LABEL_Y;
  // return dict.hasKey(hash) ? dict[hash] as Number : DEFAULT_LABEL_Y;
  var label_y = dict.hasKey(hash) ? dict[hash] : DEFAULT_LABEL_Y;
  return (label_y == null || label_y instanceof Lang.Boolean ? null : label_y) as Number?;
}

(:datafield, :datafield_hash, :datafield_label_justification, :inline)
function datafield_label_justification(hash as Number) as Number? {
  var dict = DATAFIELD_HASH_2_LABEL_JUSTIFICATION;
  // return dict.hasKey(hash) ? dict[hash] as Number : DEFAULT_LABEL_JUSTIFICATION;
  var label_justification = dict.hasKey(hash) ? dict[hash] : DEFAULT_LABEL_JUSTIFICATION;
  return (label_justification == null || label_justification instanceof Lang.Boolean ? null : label_justification) as Number?;
}
// function datafield_label_justification(hash as Number) as Number {
//   var justification = DEFAULT_LABEL_JUSTIFICATION;
//   if (HAS_DATAFIELD_HASH_2_LABEL_JUSTIFICATION) {
//     var dict = DATAFIELD_HASH_2_LABEL_JUSTIFICATION;
//     if (dict.hasKey(hash)) {
//       justification = dict[hash] as Number;
//     }
//   }
//   return justification;
// }

// data

(:datafield, :datafield_hash, :datafield_data_x, :inline)
function datafield_data_x(hash as Number) as Number? {
  var dict = DATAFIELD_HASH_2_DATA_X;
  return dict.hasKey(hash) ? dict[hash] as Number : DEFAULT_DATA_X;
  // var data_x = dict.hasKey(hash) ? dict[hash] : DEFAULT_DATA_X;
  // return (data_x == null || data_x instanceof Lang.Boolean ? null : data_x) as Number?;
}

(:datafield, :datafield_hash, :datafield_data_y, :inline)
function datafield_data_y(hash as Number) as Number? {
  var dict = DATAFIELD_HASH_2_DATA_Y;
  return dict.hasKey(hash) ? dict[hash] as Number : DEFAULT_DATA_Y;
  // var data_y = dict.hasKey(hash) ? dict[hash] : DEFAULT_DATA_Y;
  // return (data_y == null || data_y instanceof Lang.Boolean ? null : data_y) as Number?;
}

(:datafield, :datafield_hash, :datafield_data_justification, :inline)
function datafield_data_justification(hash as Number) as Number? {
  var dict = DATAFIELD_HASH_2_DATA_JUSTIFICATION;
  return dict.hasKey(hash) ? dict[hash] as Number : DEFAULT_DATA_JUSTIFICATION;
  // var data_justification = dict.hasKey(hash) ? dict[hash] : DEFAULT_DATA_JUSTIFICATION;
  // return (data_justification == null || data_justification instanceof Lang.Boolean ? null : data_justification) as Number?;
}
// function datafield_data_justification(hash as Number) as Number {
//   var justification = DEFAULT_DATA_JUSTIFICATION;
//   if (HAS_DATAFIELD_HASH_2_DATA_JUSTIFICATION) {
//     var dict = DATAFIELD_HASH_2_DATA_JUSTIFICATION;
//     if (dict.hasKey(hash)) {
//       justification = dict[hash] as Number;
//     }
//   }
//   return justification;
// }

(:datafield, :datafield_hash, :datafield_bounding_box_x, :inline)
function datafield_bounding_box_x(hash as Number) as Number? {
  var dict = DATAFIELD_HASH_2_BOUNDING_BOX_X;
  return dict.hasKey(hash) ? dict[hash] as Number : DEFAULT_BOUNDING_BOX_X;
}

(:datafield, :datafield_hash, :datafield_bounding_box_y, :inline)
function datafield_bounding_box_y(hash as Number) as Number? {
  var dict = DATAFIELD_HASH_2_BOUNDING_BOX_Y;
  return dict.hasKey(hash) ? dict[hash] as Number : DEFAULT_BOUNDING_BOX_Y;
}

(:datafield, :datafield_hash, :datafield_bounding_box_width, :inline)
function datafield_bounding_box_width(hash as Number) as Number? {
  var dict = DATAFIELD_HASH_2_BOUNDING_BOX_WIDTH;
  return dict.hasKey(hash) ? dict[hash] as Number : DEFAULT_BOUNDING_BOX_WIDTH;
}

(:datafield, :datafield_hash, :datafield_bounding_box_height, :inline)
function datafield_bounding_box_height(hash as Number) as Number? {
  var dict = DATAFIELD_HASH_2_BOUNDING_BOX_HEIGHT;
  return dict.hasKey(hash) ? dict[hash] as Number : DEFAULT_BOUNDING_BOX_HEIGHT;
}
