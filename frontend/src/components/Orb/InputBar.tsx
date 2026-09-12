import { useState } from "react";
import "./InputBar.css";

interface InputBarProps {
    onSendMessage: (text: string) => void;
}

function InputBar({ onSendMessage }: InputBarProps) {
    const [input, setInput] = useState("");

    function handleKeyDown(event: React.KeyboardEvent<HTMLInputElement>) {
        if (event.key === "Enter") {
            onSendMessage(input);
            setInput("");
        }
    }

    return (
        <div className = "input-bar">
            <input
                type = "text"
                value = {input}
                onChange = {(event) => setInput(event.target.value)}
                onKeyDown = {handleKeyDown}
                placeholder = "Enter Your Command..."
            />
        </div>
    )

}

export default InputBar;