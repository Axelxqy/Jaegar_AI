import { useRef, useState } from "react";
import "./InputBar.css";

interface InputBarProps {
    onSendMessage: (text: string) => void;
}

function InputBar({ onSendMessage }: InputBarProps) {
    const [input, setInput] = useState("");
    const textAreaRef = useRef<HTMLTextAreaElement>(null);

    function resizeTextArea() {
        const textArea = textAreaRef.current;

        if (!textArea) {
            return;
        }

        textArea.style.height = "auto";
        textArea.style.height = `${textArea.scrollHeight}px`;
    }

    function handleChange(event: React.ChangeEvent<HTMLTextAreaElement>) {
        setInput(event.target.value);
        resizeTextArea();
    }

    function handleKeyDown(event: React.KeyboardEvent<HTMLTextAreaElement>) {
        if (event.key === "Enter" && event.metaKey) {
            event.preventDefault();

            if (!input.trim()) {
                return;
            }

            onSendMessage(input);
            setInput("");

            requestAnimationFrame(() => {
                const textArea = textAreaRef.current;

                if (textArea) {
                    textArea.style.height = "auto";
                }
            });
        }
    }

    return (
        <div className = "input-bar">
            <textarea
                ref={textAreaRef}
                value = {input}
                onChange = {handleChange}
                onKeyDown = {handleKeyDown}
                placeholder = "Enter Your Command..."
                rows={1}
            />
        </div>
    )

}

export default InputBar;