import Toybox.Graphics;
import Toybox.Lang;
import Toybox.Math;
import Toybox.WatchUi;

(:no_key_hint) const KEY_HINT_ARC_WIDTH = 0;
(:key_hint) const KEY_HINT_ARC_WIDTH = 6;
(:no_key_hint) const KEY_HINT_BAR_WIDTH = 0;
(:key_hint) const KEY_HINT_BAR_WIDTH = 6;

(:no_key_id_enter) const KEY_ID_ENTER = false;
(:key_id_enter) const KEY_ID_ENTER = true;
(:no_key_id_esc) const KEY_ID_ESC = false;
(:key_id_esc) const KEY_ID_ESC = true;
(:no_key_id_menu) const KEY_ID_MENU = false;
(:key_id_menu) const KEY_ID_MENU = true;
(:no_key_id_up) const KEY_ID_UP = false;
(:key_id_up) const KEY_ID_UP = true;
(:no_key_id_down) const KEY_ID_DOWN = false;
(:key_id_down) const KEY_ID_DOWN = true;
(:no_key_id_lap) const KEY_ID_LAP = false;
(:key_id_lap) const KEY_ID_LAP = true;
(:no_key_id_start) const KEY_ID_START = false;
(:key_id_start) const KEY_ID_START = true;
(:no_key_id_clock) const KEY_ID_CLOCK = false;
(:key_id_clock) const KEY_ID_CLOCK = true;
(:no_key_id_left) const KEY_ID_LEFT = false;
(:key_id_left) const KEY_ID_LEFT = true;
(:no_key_id_right) const KEY_ID_RIGHT = false;
(:key_id_right) const KEY_ID_RIGHT = true;

(:no_key_behavior_onselect) const KEY_BEHAVIOR_ONSELECT = false;
(:key_behavior_onselect) const KEY_BEHAVIOR_ONSELECT = true;
(:no_key_behavior_onback) const KEY_BEHAVIOR_ONBACK = false;
(:key_behavior_onback) const KEY_BEHAVIOR_ONBACK = true;
(:no_key_behavior_onmenu) const KEY_BEHAVIOR_ONMENU = false;
(:key_behavior_onmenu) const KEY_BEHAVIOR_ONMENU = true;
(:no_key_behavior_previouspage) const KEY_BEHAVIOR_PREVIOUSPAGE = false;
(:key_behavior_previouspage) const KEY_BEHAVIOR_PREVIOUSPAGE = true;
(:no_key_behavior_nextpage) const KEY_BEHAVIOR_NEXTPAGE = false;
(:key_behavior_nextpage) const KEY_BEHAVIOR_NEXTPAGE = true;

(:key_location, :key_hint)
enum KeyHint {
    KEY_HINT_ENTER        = 1<<0,
    KEY_HINT_ESC          = 1<<1,
    KEY_HINT_MENU         = 1<<2,
    KEY_HINT_UP           = 1<<3,
    KEY_HINT_DOWN         = 1<<4,
    KEY_HINT_LAP          = 1<<5,
    KEY_HINT_START        = 1<<6,
    KEY_HINT_CLOCK        = 1<<7,

    KEY_HINT_ONSELECT     = 1<<8,
    KEY_HINT_ONBACK       = 1<<9,
    KEY_HINT_ONMENU       = 1<<10,
    KEY_HINT_PREVIOUSPAGE = 1<<11,
    KEY_HINT_NEXTPAGE     = 1<<12,
}

(:key_location, :key_hint)
function draw_key_hints(dc as Graphics.Dc, keyHints as KeyHint) as Void {
    if (KEY_ID_ENTER && keyHints & KEY_HINT_ENTER != 0) {
        draw_key_hint_enter(dc);
    }
    if (KEY_ID_ESC && keyHints & KEY_HINT_ESC != 0) {
        draw_key_hint_esc(dc);
    }
    if (KEY_ID_MENU && keyHints & KEY_HINT_MENU != 0) {
        draw_key_hint_menu(dc);
    }
    if (KEY_ID_UP && keyHints & KEY_HINT_UP != 0) {
        draw_key_hint_up(dc);
    }
    if (KEY_ID_DOWN && keyHints & KEY_HINT_DOWN != 0) {
        draw_key_hint_down(dc);
    }
    if (KEY_ID_LAP && keyHints & KEY_HINT_LAP != 0) {
        draw_key_hint_lap(dc);
    }
    if (KEY_ID_START && keyHints & KEY_HINT_START != 0) {
        draw_key_hint_start(dc);
    }
    if (KEY_ID_CLOCK && keyHints & KEY_HINT_CLOCK != 0) {
        draw_key_hint_clock(dc);
    }
    // if (KEY_ID_LEFT && keyHints & KEY_HINT_LEFT != 0) {
    //     draw_key_hint_left(dc);
    // }
    // if (KEY_ID_RIGHT && keyHints & KEY_HINT_RIGHT != 0) {
    //     draw_key_hint_right(dc);
    // }

    if (KEY_BEHAVIOR_ONSELECT && keyHints & KEY_HINT_ONSELECT != 0) {
        draw_key_hint_onselect(dc);
    }
    if (KEY_BEHAVIOR_ONBACK && keyHints & KEY_HINT_ONBACK != 0) {
        draw_key_hint_onback(dc);
    }
    if (KEY_BEHAVIOR_ONMENU && keyHints & KEY_HINT_ONMENU != 0) {
        draw_key_hint_onmenu(dc);
    }
    if (KEY_BEHAVIOR_PREVIOUSPAGE && keyHints & KEY_HINT_PREVIOUSPAGE != 0) {
        draw_key_hint_previouspage(dc);
    }
    if (KEY_BEHAVIOR_NEXTPAGE && keyHints & KEY_HINT_NEXTPAGE != 0) {
        draw_key_hint_nextpage(dc);
    }
}

(:key_location, :key_hint, :no_key_id_enter, :inline)
function draw_key_hint_enter(dc as Graphics.Dc) as Void {}
(:key_location, :key_hint, :personality, :key_id_enter, :inline)
function draw_key_hint_enter(dc as Graphics.Dc) as Void {
    draw_key_hint(dc, KEY_ENTER_ARC_DEGREE, KEY_ENTER_BAR_X, KEY_ENTER_BAR_Y, KEY_ENTER_BAR_WIDTH, KEY_ENTER_BAR_HEIGHT,
        Rez has :Styles ? Rez.Styles.system_loc__hint_button_right_top.x : null, Rez has :Styles ? Rez.Styles.system_loc__hint_button_right_top.y : null);
}
(:key_location, :key_hint, :no_personality, :key_id_enter, :inline)
function draw_key_hint_enter(dc as Graphics.Dc) as Void {
    draw_key_hint(dc, KEY_ENTER_ARC_DEGREE, KEY_ENTER_BAR_X, KEY_ENTER_BAR_Y, KEY_ENTER_BAR_WIDTH, KEY_ENTER_BAR_HEIGHT);
}

(:key_location, :key_hint, :no_key_id_esc, :inline)
function draw_key_hint_esc(dc as Graphics.Dc) as Void {}
(:key_location, :key_hint, :personality, :key_id_esc, :inline)
function draw_key_hint_esc(dc as Graphics.Dc) as Void {
    draw_key_hint(dc, KEY_ESC_ARC_DEGREE, KEY_ESC_BAR_X, KEY_ESC_BAR_Y, KEY_ESC_BAR_WIDTH, KEY_ESC_BAR_HEIGHT,
        Rez has :Styles ? Rez.Styles.system_loc__hint_button_right_top.x : null, Rez has :Styles ? Rez.Styles.system_loc__hint_button_right_top.y : null);
}
(:key_location, :key_hint, :no_personality, :key_id_esc, :inline)
function draw_key_hint_esc(dc as Graphics.Dc) as Void {
    draw_key_hint(dc, KEY_ESC_ARC_DEGREE, KEY_ESC_BAR_X, KEY_ESC_BAR_Y, KEY_ESC_BAR_WIDTH, KEY_ESC_BAR_HEIGHT);
}

(:key_location, :key_hint, :no_key_id_menu, :inline)
function draw_key_hint_menu(dc as Graphics.Dc) as Void {}
(:key_location, :key_hint, :personality, :key_id_menu, :inline)
function draw_key_hint_menu(dc as Graphics.Dc) as Void {
    draw_key_hint(dc, KEY_MENU_ARC_DEGREE, KEY_MENU_BAR_X, KEY_MENU_BAR_Y, KEY_MENU_BAR_WIDTH, KEY_MENU_BAR_HEIGHT,
        Rez has :Styles ? Rez.Styles.system_loc__hint_button_right_top.x : null, Rez has :Styles ? Rez.Styles.system_loc__hint_button_right_top.y : null);
}
(:key_location, :key_hint, :no_personality, :key_id_menu, :inline)
function draw_key_hint_menu(dc as Graphics.Dc) as Void {
    draw_key_hint(dc, KEY_MENU_ARC_DEGREE, KEY_MENU_BAR_X, KEY_MENU_BAR_Y, KEY_MENU_BAR_WIDTH, KEY_MENU_BAR_HEIGHT);
}

(:key_location, :key_hint, :no_key_id_up, :inline)
function draw_key_hint_up(dc as Graphics.Dc) as Void {}
(:key_location, :key_hint, :personality, :key_id_up, :inline)
function draw_key_hint_up(dc as Graphics.Dc) as Void {
    draw_key_hint(dc, KEY_UP_ARC_DEGREE, KEY_UP_BAR_X, KEY_UP_BAR_Y, KEY_UP_BAR_WIDTH, KEY_UP_BAR_HEIGHT,
        Rez has :Styles ? Rez.Styles.system_loc__hint_button_right_top.x : null, Rez has :Styles ? Rez.Styles.system_loc__hint_button_right_top.y : null);
}
(:key_location, :key_hint, :no_personality, :key_id_up, :inline)
function draw_key_hint_up(dc as Graphics.Dc) as Void {
    draw_key_hint(dc, KEY_UP_ARC_DEGREE, KEY_UP_BAR_X, KEY_UP_BAR_Y, KEY_UP_BAR_WIDTH, KEY_UP_BAR_HEIGHT);
}

(:key_location, :key_hint, :no_key_id_down, :inline)
function draw_key_hint_down(dc as Graphics.Dc) as Void {}
(:key_location, :key_hint, :personality, :key_id_down, :inline)
function draw_key_hint_down(dc as Graphics.Dc) as Void {
    draw_key_hint(dc, KEY_DOWN_ARC_DEGREE, KEY_DOWN_BAR_X, KEY_DOWN_BAR_Y, KEY_DOWN_BAR_WIDTH, KEY_DOWN_BAR_HEIGHT,
        Rez has :Styles ? Rez.Styles.system_loc__hint_button_right_top.x : null, Rez has :Styles ? Rez.Styles.system_loc__hint_button_right_top.y : null);
}
(:key_location, :key_hint, :no_personality, :key_id_down, :inline)
function draw_key_hint_down(dc as Graphics.Dc) as Void {
    draw_key_hint(dc, KEY_DOWN_ARC_DEGREE, KEY_DOWN_BAR_X, KEY_DOWN_BAR_Y, KEY_DOWN_BAR_WIDTH, KEY_DOWN_BAR_HEIGHT);
}

(:key_location, :key_hint, :no_key_id_lap, :inline)
function draw_key_hint_lap(dc as Graphics.Dc) as Void {}
(:key_location, :key_hint, :personality, :key_id_lap, :inline)
function draw_key_hint_lap(dc as Graphics.Dc) as Void {
    draw_key_hint(dc, KEY_LAP_ARC_DEGREE, KEY_LAP_BAR_X, KEY_LAP_BAR_Y, KEY_LAP_BAR_WIDTH, KEY_LAP_BAR_HEIGHT,
        Rez has :Styles ? Rez.Styles.system_loc__hint_button_right_top.x : null, Rez has :Styles ? Rez.Styles.system_loc__hint_button_right_top.y : null);
}
(:key_location, :key_hint, :no_personality, :key_id_lap, :inline)
function draw_key_hint_lap(dc as Graphics.Dc) as Void {
    draw_key_hint(dc, KEY_LAP_ARC_DEGREE, KEY_LAP_BAR_X, KEY_LAP_BAR_Y, KEY_LAP_BAR_WIDTH, KEY_LAP_BAR_HEIGHT);
}

(:key_location, :key_hint, :no_key_id_start, :inline)
function draw_key_hint_start(dc as Graphics.Dc) as Void {}
(:key_location, :key_hint, :personality, :key_id_start, :inline)
function draw_key_hint_start(dc as Graphics.Dc) as Void {
    draw_key_hint(dc, KEY_START_ARC_DEGREE, KEY_START_BAR_X, KEY_START_BAR_Y, KEY_START_BAR_WIDTH, KEY_START_BAR_HEIGHT,
        Rez has :Styles ? Rez.Styles.system_loc__hint_button_right_top.x : null, Rez has :Styles ? Rez.Styles.system_loc__hint_button_right_top.y : null);
}
(:key_location, :key_hint, :no_personality, :key_id_start, :inline)
function draw_key_hint_start(dc as Graphics.Dc) as Void {
    draw_key_hint(dc, KEY_START_ARC_DEGREE, KEY_START_BAR_X, KEY_START_BAR_Y, KEY_START_BAR_WIDTH, KEY_START_BAR_HEIGHT);
}

(:key_location, :key_hint, :no_key_id_clock, :inline)
function draw_key_hint_clock(dc as Graphics.Dc) as Void {}
(:key_location, :key_hint, :personality, :key_id_clock, :inline)
function draw_key_hint_clock(dc as Graphics.Dc) as Void {
    draw_key_hint(dc, KEY_CLOCK_ARC_DEGREE, KEY_CLOCK_BAR_X, KEY_CLOCK_BAR_Y, KEY_CLOCK_BAR_WIDTH, KEY_CLOCK_BAR_HEIGHT,
        Rez has :Styles ? Rez.Styles.system_loc__hint_button_right_top.x : null, Rez has :Styles ? Rez.Styles.system_loc__hint_button_right_top.y : null);
}
(:key_location, :key_hint, :no_personality, :key_id_clock, :inline)
function draw_key_hint_clock(dc as Graphics.Dc) as Void {
    draw_key_hint(dc, KEY_CLOCK_ARC_DEGREE, KEY_CLOCK_BAR_X, KEY_CLOCK_BAR_Y, KEY_CLOCK_BAR_WIDTH, KEY_CLOCK_BAR_HEIGHT);
}


(:key_location, :key_hint, :no_key_behavior_onselect, :inline)
function draw_key_hint_onselect(dc as Graphics.Dc) as Void {}
(:key_location, :key_hint, :personality, :key_behavior_onselect, :inline)
function draw_key_hint_onselect(dc as Graphics.Dc) as Void {
    draw_key_hint(dc, KEY_ONSELECT_ARC_DEGREE, KEY_ONSELECT_BAR_X, KEY_ONSELECT_BAR_Y, KEY_ONSELECT_BAR_WIDTH, KEY_ONSELECT_BAR_HEIGHT,
        Rez has :Styles ? Rez.Styles.system_loc__hint_button_right_top.x : null, Rez has :Styles ? Rez.Styles.system_loc__hint_button_right_top.y : null);
}
(:key_location, :key_hint, :no_personality, :key_behavior_onselect, :inline)
function draw_key_hint_onselect(dc as Graphics.Dc) as Void {
    draw_key_hint(dc, KEY_ONSELECT_ARC_DEGREE, KEY_ONSELECT_BAR_X, KEY_ONSELECT_BAR_Y, KEY_ONSELECT_BAR_WIDTH, KEY_ONSELECT_BAR_HEIGHT);
}

(:key_location, :key_hint, :no_key_behavior_onback, :inline)
function draw_key_hint_onback(dc as Graphics.Dc) as Void {}
(:key_location, :key_hint, :personality, :key_behavior_onback, :inline)
function draw_key_hint_onback(dc as Graphics.Dc) as Void {
    draw_key_hint(dc, KEY_ONBACK_ARC_DEGREE, KEY_ONBACK_BAR_X, KEY_ONBACK_BAR_Y, KEY_ONBACK_BAR_WIDTH, KEY_ONBACK_BAR_HEIGHT,
        Rez has :Styles ? Rez.Styles.system_loc__hint_button_right_bottom.x as Number? : null, Rez has :Styles ? Rez.Styles.system_loc__hint_button_right_bottom.y as Number? : null);
}
(:key_location, :key_hint, :no_personality, :key_behavior_onback, :inline)
function draw_key_hint_onback(dc as Graphics.Dc) as Void {
    draw_key_hint(dc, KEY_ONBACK_ARC_DEGREE, KEY_ONBACK_BAR_X, KEY_ONBACK_BAR_Y, KEY_ONBACK_BAR_WIDTH, KEY_ONBACK_BAR_HEIGHT);
}

(:key_location, :key_hint, :no_key_behavior_onmenu, :inline)
function draw_key_hint_onmenu(dc as Graphics.Dc) as Void {}
(:key_location, :key_hint, :personality, :key_behavior_onmenu, :inline)
function draw_key_hint_onmenu(dc as Graphics.Dc) as Void {
    draw_key_hint(dc, KEY_ONMENU_ARC_DEGREE, KEY_ONMENU_BAR_X, KEY_ONMENU_BAR_Y, KEY_ONMENU_BAR_WIDTH, KEY_ONMENU_BAR_HEIGHT,
        Rez has :Styles ? Rez.Styles.system_loc__hint_button_left_middle.x as Number? : null, Rez has :Styles ? Rez.Styles.system_loc__hint_button_left_middle.y as Number? : null);
}
(:key_location, :key_hint, :no_personality, :key_behavior_onmenu, :inline)
function draw_key_hint_onmenu(dc as Graphics.Dc) as Void {
    draw_key_hint(dc, KEY_ONMENU_ARC_DEGREE, KEY_ONMENU_BAR_X, KEY_ONMENU_BAR_Y, KEY_ONMENU_BAR_WIDTH, KEY_ONMENU_BAR_HEIGHT);
}

(:key_location, :key_hint, :no_key_behavior_previouspage, :inline)
function draw_key_hint_previouspage(dc as Graphics.Dc) as Void {}
(:key_location, :key_hint, :personality, :key_behavior_previouspage, :inline)
function draw_key_hint_previouspage(dc as Graphics.Dc) as Void {
    draw_key_hint(dc, KEY_PREVIOUSPAGE_ARC_DEGREE, KEY_PREVIOUSPAGE_BAR_X, KEY_PREVIOUSPAGE_BAR_Y, KEY_PREVIOUSPAGE_BAR_WIDTH, KEY_PREVIOUSPAGE_BAR_HEIGHT,
        Rez has :Styles ? Rez.Styles.system_loc__hint_button_left_middle.x as Number? : null, Rez has :Styles ? Rez.Styles.system_loc__hint_button_left_middle.y as Number? : null);
}
(:key_location, :key_hint, :no_personality, :key_behavior_previouspage, :inline)
function draw_key_hint_previouspage(dc as Graphics.Dc) as Void {
    draw_key_hint(dc, KEY_PREVIOUSPAGE_ARC_DEGREE, KEY_PREVIOUSPAGE_BAR_X, KEY_PREVIOUSPAGE_BAR_Y, KEY_PREVIOUSPAGE_BAR_WIDTH, KEY_PREVIOUSPAGE_BAR_HEIGHT);
}

(:key_location, :key_hint, :no_key_behavior_nextpage, :inline)
function draw_key_hint_nextpage(dc as Graphics.Dc) as Void {}
(:key_location, :key_hint, :personality, :key_behavior_nextpage, :inline)
function draw_key_hint_nextpage(dc as Graphics.Dc) as Void {
    draw_key_hint(dc, KEY_NEXTPAGE_ARC_DEGREE, KEY_NEXTPAGE_BAR_X, KEY_NEXTPAGE_BAR_Y, KEY_NEXTPAGE_BAR_WIDTH, KEY_NEXTPAGE_BAR_HEIGHT,
        Rez has :Styles ? Rez.Styles.system_loc__hint_button_left_bottom.x as Number? : null, Rez has :Styles ? Rez.Styles.system_loc__hint_button_left_bottom.y as Number? : null);
}
(:key_location, :key_hint, :no_personality, :key_behavior_nextpage, :inline)
function draw_key_hint_nextpage(dc as Graphics.Dc) as Void {
    draw_key_hint(dc, KEY_NEXTPAGE_ARC_DEGREE, KEY_NEXTPAGE_BAR_X, KEY_NEXTPAGE_BAR_Y, KEY_NEXTPAGE_BAR_WIDTH, KEY_NEXTPAGE_BAR_HEIGHT);
}

(:key_location, :key_hint, :personality)
function draw_key_hint(dc as Graphics.Dc, degree as Float, barX as Number, barY as Number, barW as Number, barH as Number
// , x as Number, y as Number, width as Number, height as Number
, styleX as Number?, styleY as Number? /*, styleW as Number, styleH as Number*/
) as Void {
    if (DEBUG_LAYOUT && styleX != null && styleY != null) {
    // var x0 = x + width / 2;
    // var y0 = y + height / 2;
    // log("drawKeyHint: x: " + x + ", y: " + y + ", w: " + width + ", h: " + height + ", SHAPE_RECTANGLE: " + SHAPE_RECTANGLE + ", SHAPE_ROUND: " + SHAPE_ROUND);
    // dc.setPenWidth(1);
    // dc.drawLine(dc.getWidth()/2, dc.getHeight()/2, x0, y0);
    // dc.drawCircle(x0, y0, max(width, height) / 2);
    // dc.drawCircle(styleX, styleY, 20);
        dc.setPenWidth(1);
        dc.drawRectangle(styleX, styleY, Rez.Styles.system_size__menu_icon.scaleX, Rez.Styles.system_size__menu_icon.scaleY);
    }

    if (KEY_HINT_IS_ARC) {
        if (DEBUG_LAYOUT) {
            dc.setColor(Graphics.COLOR_GREEN, Graphics.COLOR_TRANSPARENT);
        }
        dc.setPenWidth(KEY_HINT_ARC_WIDTH);
        dc.drawArc(dc.getWidth() / 2, dc.getHeight() / 2, dc.getWidth() / 2 - 3, Graphics.ARC_COUNTER_CLOCKWISE, degree - 8, degree + 8);

        if (styleX != null && styleY != null) {
            var adjustDir = styleX >= dc.getWidth() / 2 ? 1 : -2;
            var rad = Math.atan2(styleY + adjustDir * Rez.Styles.system_size__menu_icon.scaleY / 2 - dc.getHeight() / 2, styleX /*+ Rez.Styles.system_size__menu_icon.scaleX / 2*/ - dc.getWidth() / 2);
            var deg = Math.toDegrees(rad);
            log("draw_style_key_hint: x: " + styleX + ", y: " + styleY + ", rad: " + rad + ", deg: " + deg);
            if (DEBUG_LAYOUT) {
                dc.setColor(Graphics.COLOR_BLUE, Graphics.COLOR_TRANSPARENT);
            }
            // dc.drawArc(dc.getWidth() / 2, dc.getHeight() / 2, dc.getWidth() / 2 - 3, Graphics.ARC_COUNTER_CLOCKWISE, degree - 7, degree + 7);
            dc.drawArc(dc.getWidth() / 2, dc.getHeight() / 2, dc.getWidth() / 2 - 3 - 6, Graphics.ARC_COUNTER_CLOCKWISE, deg - 8, deg + 8);
        }
    }
    if (KEY_HINT_IS_BAR || (KEY_HINT_IS_ARC && barW > 0)) {
        dc.setPenWidth(KEY_HINT_BAR_WIDTH);
        dc.drawRectangle(barX, barY, barW, barH);
    }
}
(:key_location, :key_hint, :no_personality)
function draw_key_hint(dc as Graphics.Dc, degree as Float, barX as Number, barY as Number, barW as Number, barH as Number) as Void {
    if (DEBUG_LAYOUT) {
    // var x0 = x + width / 2;
    // var y0 = y + height / 2;
    // log("drawKeyHint: x: " + x + ", y: " + y + ", w: " + width + ", h: " + height + ", SHAPE_RECTANGLE: " + SHAPE_RECTANGLE + ", SHAPE_ROUND: " + SHAPE_ROUND);
    // dc.setPenWidth(1);
    // dc.drawLine(dc.getWidth()/2, dc.getHeight()/2, x0, y0);
    // dc.drawCircle(x0, y0, max(width, height) / 2);
    // dc.drawCircle(styleX, styleY, 20);
        // dc.setPenWidth(1);
    }

    if (KEY_HINT_IS_ARC) {
        if (DEBUG_LAYOUT) {
            dc.setColor(Graphics.COLOR_GREEN, Graphics.COLOR_TRANSPARENT);
        }
        dc.setPenWidth(KEY_HINT_ARC_WIDTH);
        var halfWidth = dc.getWidth() / 2;
        dc.drawArc(halfWidth, dc.getHeight() / 2, halfWidth /*- (KEY_HINT_ARC_WIDTH - 1) / 2*/, Graphics.ARC_COUNTER_CLOCKWISE, degree - 8, degree + 8);
    }
    if (KEY_HINT_IS_BAR || (KEY_HINT_IS_ARC && barW > 0)) {
        dc.setPenWidth(KEY_HINT_BAR_WIDTH);
        dc.drawRectangle(barX, barY, barW, barH);
        // log("draw_key_hint: barX: " + barX + ", barY: " + barY + ", barW:" + barW + ", barH:" + barH);
    }
}

            // log("hint: sx: " + Rez.Styles.system_size__menu_icon.scaleX + ", sy: " +  + Rez.Styles.system_size__menu_icon.scaleY);
    // Rez.Styles.system_loc__hint_button_left_top
    // Rez.Styles.system_loc__hint_button_left_middle
    // Rez.Styles.system_loc__hint_button_left_bottom
    // Rez.Styles.system_loc__hint_button_right_top
    // Rez.Styles.system_loc__hint_button_right_middle
    // Rez.Styles.system_loc__hint_button_right_bottom
                // Rez.Styles.system_loc__hint_button_right_top.exclude
                // Rez.Styles.system_loc__hint_button_right_top.horizontalJustification
                // Rez.Styles.system_loc__hint_button_right_top.verticalJustification
            //     Rez.Styles.system_size__menu_icon.scaleX
            // Rez.Styles.system_size__menu_icon.scaleX
            // Rez.Drawables.system_icon_positive__hint_action_menu
            // Rez.Styles.confirmation_loc__hint_confirm.x
            // Rez.Styles.system_icon_positive__hint_button_left_bottom.filename
            // Rez.Styles.system_icon_positive__hint_button_left_bottom.
            // Rez.Styles.device_info
            // Rez.Styles.system_icon_dark__cancel
            // draw_style_key_hint(dc, :system_loc__hint_button_left_top);
            // draw_style_key_hint(dc, :system_loc__hint_button_left_middle);

// function draw_style_key_hint(dc as Graphics.Dc, keyHintSymbol as Symbol) as Void {
//     // var hint = Rez.Styles[keyHintSymbol];
//     // log("draw_style_key_hint: x: " + hint.x + ", y: " + hint.y);
//     // var d = Rez.Styles.system_loc__hint_button_left_middle;
//     // var a = Rez.Strings.AppName;
//     // var b = Rez.Strings[:AppName];
//     // var s = Rez.Strings;
//     // var t = Rez.Styles;
//     var x = Rez.Styles.system_loc__hint_button_left_middle.x;
//     var y = Rez.Styles.system_loc__hint_button_left_middle.y;
//     // var x = Rez.Styles[:system_loc__hint_button_left_middle].x;
//     // var y = Rez.Styles[:system_loc__hint_button_left_middle].y;
//     // var styles = Rez.Styles;
//     // var x = styles.system_loc__hint_button_left_middle.x as Number;
//     // var y = styles.system_loc__hint_button_left_middle.y as Number;
//     log("draw_style_key_hint: x: " + x + ", y: " + y);
//     // log("draw_style_key_hint: x: " + d.x + ", y: " + d.y);
//     if (KEY_HINT_IS_ARC) {
//         dc.setPenWidth(4);
//         var rad = Math.atan2(x - dc.getWidth() / 2, y - dc.getHeight() / 2);
//         var degree = Math.toDegrees(rad);
//         log("draw_style_key_hint: x: " + x + ", y: " + y + ", rad: " + rad + ", deg: " + degree);
//         dc.setColor(Graphics.COLOR_BLUE, Graphics.COLOR_TRANSPARENT);
//         // dc.drawArc(dc.getWidth() / 2, dc.getHeight() / 2, dc.getWidth() / 2 - 3, Graphics.ARC_COUNTER_CLOCKWISE, degree - 7, degree + 7);
//         dc.drawArc(dc.getWidth() / 2, dc.getHeight() / 2, dc.getWidth() / 2 - 3, Graphics.ARC_COUNTER_CLOCKWISE, degree - 7, degree + 7);
//     }
// }

// // (:exclude)
// function getPersonalityUI(personalityUiType as Symbol, bgColor as Number) as Array? {
//     if (!(Rez has :Styles)) {
//         return null;
//     }
//     // Rez.Styles.system_loc__hint_button_left_top
//     // Rez.Styles.system_loc__hint_button_left_middle
//     // Rez.Styles.system_loc__hint_button_left_bottom
//     // Rez.Styles.system_loc__hint_button_right_top
//     // Rez.Styles.system_loc__hint_button_right_middle
//     // Rez.Styles.system_loc__hint_button_right_bottom
//     switch (personalityUiType) {
//         case :hint_bottom_right:
//             // var backButtonHint = null;
//             // if (bgColor != Graphics.COLOR_BLACK) {
//             //     backButtonHint = (WatchUi.loadResource(Rez.Drawables.PersonalityHintBottomRightLight) as BitmapResource);
//             // } else {
//             //     backButtonHint = (WatchUi.loadResource(Rez.Drawables.PersonalityHintBottomRightDark) as BitmapResource);
//             // }
//             // return ([Rez.Styles.system_loc__hint_button_right_bottom.x, Rez.Styles.system_loc__hint_button_right_bottom.y, backButtonHint] as Array<Number or BitmapResource>);
//             return ([Rez.Styles.system_loc__hint_button_right_bottom.x, Rez.Styles.system_loc__hint_button_right_bottom.y] as Array<Number>);
//     }
//     return (null);
// }

    // fenix6:
    // "display": {
    //     "behaviors": [],
    //     "isTouch": false,
    //     "landscapeOrientation": 0,
    //     "location": {
    //         "height": 260,
    //         "width": 260,
    //         "x": 72,
    //         "y": 138
    //     },
    //     "shape": "round"
    // },

        // {
        //     "behavior": "onSelect",
        //     "id": "enter",
        //     "location": {
        //         "height": 48,
        //         "width": 40,
        //         "x": 352,
        //         "y": 147
        //     }
        // },