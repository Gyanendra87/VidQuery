document.addEventListener("DOMContentLoaded", () => {
  const askBtn = document.getElementById("askBtn");
  const videoIdInput = document.getElementById("videoId");
  const questionInput = document.getElementById("question");
  const answerDiv = document.getElementById("answer");

  askBtn.addEventListener("click", async () => {
    const videoId = videoIdInput.value.trim();
    const question = questionInput.value.trim();

    // Validate input
    if (!videoId || !question) {
      answerDiv.textContent = "⚠️ Please enter both video ID and question.";
      return;
    }

    // Show loading and disable button
    answerDiv.textContent = "⏳ Thinking...";
    askBtn.disabled = true;
    askBtn.textContent = "Processing...";

    try {
      const response = await fetch("http://127.0.0.1:8000/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ video_id: videoId, question })
      });

      if (!response.ok) {
        // Handle backend errors gracefully
        if (response.status === 404) {
          throw new Error("Transcript not available for this video.");
        }
        throw new Error(`Server error: ${response.status}`);
      }

      const data = await response.json();
      console.log("Backend Response:", data);
      answerDiv.textContent = data.answer?.trim() || "🤔 No answer found.";
    } catch (error) {
      console.error("Error fetching answer:", error);
      if (error.message.includes("Failed to fetch")) {
        answerDiv.textContent = "❌ Cannot connect to backend. Is it running?";
      } else {
        answerDiv.textContent = `❌ ${error.message}`;
      }
    } finally {
      // Re-enable button
      askBtn.disabled = false;
      askBtn.textContent = "Ask";
    }
  });
});
