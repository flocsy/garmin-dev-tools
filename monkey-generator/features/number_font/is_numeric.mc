import Toybox.Lang;

(:no_check_numeric, :inline) // only to make the compiler happy
function is_numeric(str as String) as Boolean {
    return true;
}
(:no_ciq_1_3_0, :check_numeric, :inline) // only epix
function is_numeric(str as String) as Boolean {
    return false;
}
(:ciq_1_3_0, :check_numeric, :inline)
function is_numeric(str as String) as Boolean {
    var result = true;
    if (!NUMERIC_CHARS_UNKNOWN) {
        var chars = str.toCharArray(); // api 1.3.0
        for (var i = chars.size() - 1; i >= 0; i--) {
            // var char = chars[i];
            // if ('0' <= char && char <= '9') { // 6471 = +46
            //     // continue;
            // } else if (NUMBER_FONT_HAS_LOWER_CASE_ABC && 'a' <= char && char <= 'z') {
            //     // continue;
            // } else if (NUMBER_FONT_HAS_UPPER_CASE_ABC && 'A' <= char && char <= 'A') {
            //     // continue;
            // }
            // else if (NUMERIC_CHARS.find("" + char) == null) { // 6425

            // if (NUMERIC_CHARS.find(char.toString()) == null) { // 6428
            if (NUMERIC_CHARS.find("" + chars[i]) == null) { // 6425
                result = false;
                break; // +3
            }
        }
    }
    return result;
}
// 6425,1981

// (:inline)
// function is_numeric(str as String) as Boolean {
//     var result;
//     if (String has :toCharArray) {
//         var chars = str.toCharArray(); // api 1.3.0
//         result = true;
//         for (var i = chars.size() - 1; i >= 0; i--) {
//             if (NUMERIC_CHARS.find("" + chars[i]) == null) {
//                 result = false;
//                 // break; // +3
//             }
//         }
//     } else {
//         result = false;
//     }
//     return result;
// }
