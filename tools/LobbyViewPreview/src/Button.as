package  {

    import flash.display.Sprite;
    import flash.text.TextField;
    import flash.events.Event;
    import flash.events.MouseEvent;

    public class Button extends Sprite {

        public static const CLICKED:String = "clicked";

        private var textfield:TextField;
        private var _padding:Number = 10;
        private var _onMouseOver:Boolean = false;
        private var _pressed:Boolean = false;

        public function Button(label:String) {
            super();
            textfield = new TextField();
            textfield.text = label;
            textfield.selectable = false;
            addChild(textfield);
            addEventListener(Event.ADDED_TO_STAGE, refresh);
            addEventListener(MouseEvent.MOUSE_OVER, function(event:MouseEvent):void {
                _onMouseOver = true;
                refresh();
            });
            addEventListener(MouseEvent.MOUSE_OUT, function(event:MouseEvent):void {
                _onMouseOver = false;
                refresh();
            });
            addEventListener(MouseEvent.MOUSE_DOWN, function(event:MouseEvent):void {
                _pressed = true;
                refresh();
            });
            addEventListener(MouseEvent.MOUSE_UP, function(event:MouseEvent):void {
                _pressed = false;
                refresh();
            });
            addEventListener(MouseEvent.CLICK, function(event:MouseEvent):void {
                dispatchEvent(new Event(CLICKED));
            });
        }

        override public function get width():Number {
            return textfield.textWidth + _padding * 2 + 10;
        }

        override public function set width(value:Number):void {
        }

        override public function get height():Number {
            return textfield.textHeight + _padding * 2 + 5;
        }

        override public function set height(value:Number):void {
        }

        private function refresh(event:Event = null):void {
            textfield.width = width - _padding * 2;
            textfield.height = height - _padding * 2;
            textfield.x = _padding + textOffset;
            textfield.y = _padding + textOffset;

            with (graphics) {
                beginFill(backgroundColor);
                drawRect(0,0, width, height);
                endFill();
                lineStyle(1, borderColor, 100);
                drawRect(0, 0, width, height);
            }
        }

        private function get textOffset():Number {
            if (_pressed) {
                return 1;
            } else {
                return 0;
            }
        }

        private function get backgroundColor():Number {
            if (_onMouseOver) {
                return 0xE5F1FB;
            } else {
                return 0xE1E1E1;
            }
        }

        private function get borderColor():Number {
            if (_onMouseOver) {
                return 0x0078D7;
            } else {
                return 0x808080;
            }
        }
    }
}
