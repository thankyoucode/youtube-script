import sys
import re
from youtube_transcript_api import YouTubeTranscriptApi
from yt_dlp import YoutubeDL
import os

class YTTranscriptText:
    def __init__(self, url:str, dir:str):
        self.url:str = url
        self.dir = dir
        self.video_id:str
        self.title:str
        self.description:str
        self.transcript:list[object] = []
        self.transcript_text:list[str] = []
        self.transcript_paragraphs:list[str] = []


    def get_metadata(self):
        with YoutubeDL({'quiet': True, 'skip_download': True}) as ydl:
            info_dict = ydl.extract_info(self.url, download=False)
            self.video_id = info_dict.get('id')
            self.title = info_dict.get('title', 'untitled')
            self.description = info_dict.get('description', '')

    def get_transcript(self):
        # getting subtitle from youtube: list[dict]
        self.transcript = YouTubeTranscriptApi.get_transcript(self.video_id)
        # get text from each dict and make list of that test: list[str]
        self.transcript_text = [subtitle["text"] for subtitle in self.transcript]


    @staticmethod
    def sanitize_filename(title):
        # Remove/replace invalid filename characters
        return re.sub(r'[\\/*?:"<>|]', '_', title).strip()
    
    def list_to_paragraphs(self, min_length=400) -> list[str]:
        """
        input: list[str] here str is a short video caption
        output: list[str] here str is a paragraphs
        """
        current = ''
        count = 0
        for line in self.transcript_text:
            # Always add a space before new line content, unless starting out
            if current:
                current += ' '
            current += line
            count += len(line) + 1  # Add 1 for the space
            if (line.strip().endswith(('.', '?', '!')) and count >= min_length):
                self.transcript_paragraphs.append(current.strip())
                current = ''
                count = 0
        if current:
            self.transcript_paragraphs.append(current.strip())
    
    def write_markdown(self):
        safe_title = self.sanitize_filename(self.title)
        filepath = os.path.join(self.dir, f"{safe_title}.md")

        # Write YAML front matter and transcript to file
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("---\n")
            f.write(f"video: https://www.youtube.com/watch?v={self.video_id}\n")
            f.write(f"title: \"{self.title.replace('\"','\\\"')}\"\n")
            f.write("description: |\n")
            for line in self.description.splitlines():
                f.write(f"  {line}\n")
            f.write("---\n\n")
            for paragraph in self.transcript_paragraphs:
                f.write(f"\n\n{paragraph}")
    
    def download(self):
        self.get_metadata()
        self.get_transcript()
        self.list_to_paragraphs()
        self.write_markdown()

def main():
    if len(sys.argv) < 2:
        print(f"Usage: python {sys.argv[0]} <video_id>")
        sys.exit(1)

    url = sys.argv[1]
    yt = YTTranscriptText(url, dir="download/transcript")
    yt.download()

if __name__ == "__main__":
    main()
