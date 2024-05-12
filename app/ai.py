from openai import OpenAI


class AI:
    __assistant_instructions = """
    You are a helpful assistant answering questions about PDFs and YouTube videos.
    """

    def __init__(
        self,
        openai_api_key: str,
        assistant_name: str,
        vector_store_name: str,
        assistant_instructions: str = None,
    ):
        self.assistant_name = assistant_name
        self.vector_store_name = vector_store_name

        self.openai = OpenAI(api_key=openai_api_key)
        self.assistant = None
        self.vector_store = None
        self.thread = None
        self.__is_ready = False

        self.assistant_instructions = (
            assistant_instructions
            if assistant_instructions is not None
            else AI.__assistant_instructions
        )

    def __create_vector_store(self):
        vector_stores = self.openai.beta.vector_stores.list()
        for vector_store in vector_stores.data:
            if vector_store.name == self.vector_store_name:
                return vector_store

        vector_store = self.openai.beta.vector_stores.create(
            name=self.vector_store_name
        )
        return vector_store

    def __create_assistant(self):
        all_assistants = self.openai.beta.assistants.list()

        for assistant in all_assistants:
            if assistant.name == self.assistant_name:
                return assistant

        vector_store_id = self.__get_vector_store().id
        assistant = self.openai.beta.assistants.create(
            name=self.assistant_name,
            tools=[{"type": "file_search"}],
            model="gpt-4-turbo",
            tool_resources={"file_search": {"vector_store_ids": [vector_store_id]}},
        )
        return assistant

    def __get_assistant(self):
        if self.assistant is None:
            self.assistant = self.__create_assistant()
        return self.assistant

    def __get_vector_store(self):
        if self.vector_store is None:
            self.vector_store = self.__create_vector_store()
        return self.vector_store

    def upload_file_stream(self, file_path: str):
        file_paths = [file_path]
        file_streams = [open(path, "rb") for path in file_paths]

        batch = self.openai.beta.vector_stores.file_batches.upload_and_poll(
            vector_store_id=self.__get_vector_store().id, files=file_streams
        )

        if batch.status != "completed" or batch.file_counts.failed > 0:
            raise Exception("Failed to upload file to vector store")

    def is_ready(self) -> bool:
        if self.__is_ready:
            return True

        vector_store = self.__get_vector_store()

        vector_store_files = self.openai.beta.vector_stores.files.list(
            vector_store_id=vector_store.id, limit=1
        )
        self.__is_ready = len(vector_store_files.data) > 0
        return self.__is_ready

    def ask(self, question: str) -> str:
        if self.thread is None:
            self.thread = self.openai.beta.threads.create()

        message = self.openai.beta.threads.messages.create(
            thread_id=self.thread.id, role="user", content=question
        )

        self.openai.beta.threads.runs.create_and_poll(
            thread_id=self.thread.id, assistant_id=self.__get_assistant().id
        )

        messages = self.openai.beta.threads.messages.list(thread_id=self.thread.id)
        for message in messages.data:
            for content in message.content:
                message = content.text.value
                return message

    def clear_vector_store_and_reset_thread(self):
        vector_store = self.__get_vector_store()
        more_files = True
        try:
            while more_files:
                vector_store_files = self.openai.beta.vector_stores.files.list(
                    vector_store_id=vector_store.id
                )
                if not vector_store_files.data:
                    more_files = False
                else:
                    for file in vector_store_files.data:
                        self.openai.beta.vector_stores.files.delete(
                            vector_store_id=vector_store.id, file_id=file.id
                        )
        except Exception as e:
            pass  # The API sometimes returns 404 errors because it lists files that no longer exist (it's a beta version, isn't it?)

        self.thread = None
        self.__is_ready = False
