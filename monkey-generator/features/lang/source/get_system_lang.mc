import Toybox.Lang;
import Toybox.System;
import Toybox.WatchUi;

(:no_system_lang, :lang2)
function get_system_lang2() as String {
    return WatchUi.loadResource(Rez.Strings.lang2) as String;
}
(:no_system_lang, :lang3)
function get_system_lang3() as String {
    return WatchUi.loadResource(Rez.Strings.lang3) as String;
}

// (:system_lang, :lang3)
// const LANGUAGE_2_STRING = {
//     LANGUAGE_ARA => "ara", // Arabic
//     LANGUAGE_BUL => "bul", // Bulgarian
//     LANGUAGE_CES => "ces", // Czech
//     LANGUAGE_CHS => "chs", // Chinese (Simplified)
//     LANGUAGE_CHT => "cht", // Chinese (Traditional)
//     LANGUAGE_DAN => "dan", // Danish
//     LANGUAGE_DEU => "deu", // German
//     LANGUAGE_DUT => "dut", // Dutch
//     LANGUAGE_ENG => "eng", // English
//     LANGUAGE_EST => "est", // Estonian
//     LANGUAGE_FIN => "fin", // Finnish
//     LANGUAGE_FRE => "fre", // French
//     LANGUAGE_GRE => "gre", // Greek
//     LANGUAGE_HEB => "heb", // Hebrew
//     LANGUAGE_HRV => "hrv", // Croatian
//     LANGUAGE_HUN => "hun", // Hungarian
//     LANGUAGE_IND => "ind", // Bahasa Indonesia
//     LANGUAGE_ITA => "ita", // Italian
//     LANGUAGE_JPN => "jpn", // Japanese
//     LANGUAGE_KOR => "kor", // Korean
//     LANGUAGE_LAV => "lav", // Latvian
//     LANGUAGE_LIT => "lit", // Lithuanian
//     LANGUAGE_NOB => "nob", // Norwegian
//     LANGUAGE_POL => "pol", // Polish
//     LANGUAGE_POR => "por", // Portuguese
//     LANGUAGE_RON => "ron", // Romanian
//     LANGUAGE_RUS => "rus", // Russian
//     LANGUAGE_SLO => "slo", // Slovak
//     LANGUAGE_SLV => "slv", // Slovenian
//     LANGUAGE_SPA => "spa", // Spanish
//     LANGUAGE_SWE => "swe", // Swedish
//     LANGUAGE_THA => "tha", // Thai
//     LANGUAGE_TUR => "tur", // Turkish
//     LANGUAGE_UKR => "ukr", // Ukrainian
//     LANGUAGE_VIE => "vie", // Vietnamese
//     LANGUAGE_ZSM => "zsm", // Standard (Bahasa) Malay
// ] as Dictionary<System.Language, String>;
// (:system_lang, :lang3)
// function get_system_lang3() as String {
//     return LANGUAGE_2_STRING[System.getDeviceSettings().systemLanguage];
// }

// const LANGUAGE_2_STRING = {
//     8389920 => "ara", // Arabic
//     8389921 => "bul", // Bulgarian
//     8389352 => "ces", // Czech
//     8389372 => "chs", // Chinese (Simplified)
//     8389371 => "cht", // Chinese (Traditional)
//     8389353 => "dan", // Danish
//     8389358 => "deu", // German
//     8389354 => "dut", // Dutch
//     8389355 => "eng", // English
//     8390796 => "est", // Estonian
//     8389356 => "fin", // Finnish
//     8389357 => "fre", // French
//     8389359 => "gre", // Greek
//     8389919 => "heb", // Hebrew
//     8389361 => "hrv", // Croatian
//     8389360 => "hun", // Hungarian
//     8389578 => "ind", // Bahasa Indonesia
//     8389362 => "ita", // Italian
//     8389373 => "jpn", // Japanese
//     8389696 => "kor", // Korean
//     8390797 => "lav", // Latvian
//     8390798 => "lit", // Lithuanian
//     8389363 => "nob", // Norwegian
//     8389364 => "pol", // Polish
//     8389365 => "por", // Portuguese
//     8390799 => "ron", // Romanian
//     8389366 => "rus", // Russian
//     8389367 => "slo", // Slovak
//     8389368 => "slv", // Slovenian
//     8389369 => "spa", // Spanish
//     8389370 => "swe", // Swedish
//     8389548 => "tha", // Thai
//     8389774 => "tur", // Turkish
//     8390800 => "ukr", // Ukrainian
//     8390206 => "vie", // Vietnamese
//     8389579 => "zsm", // Standard (Bahasa) Malay
// ] as Dictionary<System.Language, String>;
