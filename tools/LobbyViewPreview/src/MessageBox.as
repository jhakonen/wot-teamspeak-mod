package  {

    import flash.display.Sprite;
    import flash.text.TextField;
    import flash.events.Event;

    public class MessageBox extends Sprite {

        private var textfield:TextField;
        private var _padding:Number = 20;
        private var _backgroundColor:Number = 0xFFAAAA;
        private var _width:Number = 0;
        private var _height:Number = 0;
        private var _buttons:Array = [];

        public function MessageBox(width:Number, height:Number, buttons:Array, label:String) {
            super();

            textfield = new TextField();
            textfield.text = label;
            textfield.wordWrap = true;

            addChild(textfield);

            for each(var name:String in buttons) {
                var button:Button = new Button(name);
                button.addEventListener(Button.CLICKED, createButtonClickDispatcher(name));
                _buttons.push(button);
                addChild(button);
            }

            _width = width;
            _height = height;

            addEventListener(Event.ADDED_TO_STAGE, refresh);
        }

        private function createButtonClickDispatcher(name:String):Function {
            return function(event:Event):void {
                dispatchEvent(new Event(name));
            }
        }

        override public function get width():Number
        {
            return _width;
        }

        override public function set width(value:Number):void
        {
            _width = value;
        }

        override public function get height():Number
        {
            return _height;
        }

        override public function set height(value:Number):void
        {
            _height = value;
        }

        private function refresh(event:Event = null):void {
            x = (stage.stageWidth - width) / 2;
            y = (stage.stageHeight - height) / 2;

            textfield.width = width - _padding * 2;
            textfield.height = height - _padding * 2;
            textfield.x = _padding;
            textfield.y = _padding;

            with (graphics) {
                // drawing a white rectangle
                beginFill(_backgroundColor);
                drawRect(0,0, width, height);
                endFill();
                // drawing a black border
                lineStyle(2, 0x000000, 100);
                drawRect(0, 0, width, height);
            }

            var button:Button;
            var totalWidth:Number = 0;
            for each(button in _buttons) {
                totalWidth += button.width;
            }
            var buttonPadding:Number = (width - totalWidth) / (_buttons.length + 1);
            var xOffset:Number = 0;
            for each(button in _buttons) {
                button.x = xOffset + buttonPadding;
                button.y = height - button.height - _padding;
                xOffset += button.width + buttonPadding;
            }
        }
    }
}