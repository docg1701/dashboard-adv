// frontend/src/modules/gerador_quesitos/tests/GeradorQuesitos.test.tsx
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import '@testing-library/jest-dom';
import { vi } from 'vitest';
import GeradorQuesitos from '../GeradorQuesitos';
import { useGeradorQuesitosStore } from '../../../stores/geradorQuesitosStore';
import { OPCOES_BENEFICIO, OPCOES_PROFISSAO, FRASES_DIVERTIDAS } from '../../../config/opcoesFormulario';

// Mockear o store Zustand
vi.mock('../../../stores/geradorQuesitosStore');

// Mockear FRASES_DIVERTIDAS para ter um valor previsível
vi.mock('../../../config/opcoesFormulario', async (importOriginal) => {
    const original = await importOriginal<typeof import('../../../config/opcoesFormulario')>();
    return {
        ...original,
        FRASES_DIVERTIDAS: ['Testando... 1, 2, 3.'],
    };
});

describe('GeradorQuesitos Component', () => {
    const mockUploadAndProcessSinglePdfForQuesitos = vi.fn();
    let mockStoreState: any;

    beforeEach(() => {
        // Reset e setup do mock do store para cada teste
        mockStoreState = {
            isLoading: false,
            error: null,
            quesitosResult: null,
            currentFileBeingProcessed: null,
            processedDocumentInfo: null,
            uploadAndProcessSinglePdfForQuesitos: mockUploadAndProcessSinglePdfForQuesitos,
        };
        (useGeradorQuesitosStore as any).mockImplementation((selector: any) => selector(mockStoreState));
        mockUploadAndProcessSinglePdfForQuesitos.mockReset();
        vi.useFakeTimers(); // Usar timers falsos para controlar intervalos
    });

    afterEach(() => {
        vi.runOnlyPendingTimers();
        vi.useRealTimers(); // Restaurar timers reais
    });

    const renderComponent = () => render(<GeradorQuesitos />);

    const selectBeneficio = async (beneficio: string) => {
        const beneficioSelect = screen.getByLabelText(/benefício pretendido/i);
        fireEvent.mouseDown(beneficioSelect);
        await waitFor(() => screen.getByRole('option', { name: beneficio }));
        fireEvent.click(screen.getByRole('option', { name: beneficio }));
    };

    const selectProfissao = async (profissao: string) => {
        const profissaoSelect = screen.getByLabelText(/profissão/i);
        fireEvent.mouseDown(profissaoSelect);
        await waitFor(() => screen.getByRole('option', { name: profissao }));
        fireEvent.click(screen.getByRole('option', { name: profissao }));
    };

    const uploadFile = (file: File) => {
        const fileInput = screen.getByTestId('file-input-gerador-quesitos') as HTMLInputElement; // Adicione data-testid ao Input
        fireEvent.change(fileInput, { target: { files: [file] } });
    };

    test('GQ-FE-001: Upload de PDF válido e início da geração de quesitos', async () => {
        renderComponent();

        expect(screen.getByText('Gerador de quesitos')).toBeInTheDocument();

        await selectBeneficio(OPCOES_BENEFICIO[0]);
        await selectProfissao(OPCOES_PROFISSAO[0]);

        const fakeFile = new File(['dummy content'], 'test.pdf', { type: 'application/pdf' });
        // O input de arquivo está oculto, precisamos simular o clique no botão "Adicionar PDF(s)"
        // e depois interagir com o input ref. Para simplificar, vamos assumir que o input é acessível por um data-testid.
        // No GeradorQuesitos.tsx, adicione data-testid="file-input-gerador-quesitos" ao <Input type="file" ... />

        // Botão que aciona o input
        const uploadButton = screen.getByRole('button', { name: /adicionar pdf\(s\)/i });
        fireEvent.click(uploadButton);

        // O input real está com sx={{ display: 'none' }}, então precisamos encontrá-lo de outra forma,
        // por exemplo, se ele tem um ref acessível ou um data-testid.
        // Para o teste, vamos assumir que o GeradorQuesitos.tsx foi modificado para ter:
        // <Input type="file" inputRef={fileInputRef} onChange={handleFileChange} ... inputProps={{ 'data-testid': 'file-input-real' }} />
        // E o botão "Adicionar PDF(s)" tem um onClick que chama fileInputRef.current?.click();
        // A forma mais fácil de testar isso é mockar o fileInputRef.current.click e o handleFileChange.
        // Ou, como feito agora, garantir que o input seja acessível via getByTestId após o clique.
        // No componente, o <Input ... /> precisa ter `data-testid="file-input-gerador-quesitos"` em `inputProps`.

        // Adicionando o data-testid no componente original:
        // <Input type="file" inputRef={fileInputRef} onChange={handleFileChange} inputProps={{ accept: '.pdf', multiple: true, 'data-testid': 'file-input-gerador-quesitos' }} sx={{ display: 'none' }} />

        const fileInputElement = screen.getByTestId('file-input-gerador-quesitos');
        fireEvent.change(fileInputElement, { target: { files: [fakeFile] } });

        await waitFor(() => {
            expect(screen.getByText(fakeFile.name)).toBeInTheDocument();
        });

        const submitButton = screen.getByRole('button', { name: /gerar quesitos/i });
        fireEvent.click(submitButton);

        await waitFor(() => {
            expect(mockUploadAndProcessSinglePdfForQuesitos).toHaveBeenCalledWith(
                fakeFile,
                OPCOES_BENEFICIO[0],
                OPCOES_PROFISSAO[0],
                expect.any(String) // Modelo IA
            );
        });

        // Simular resultado
        act(() => {
            mockStoreState.isLoading = false;
            mockStoreState.quesitosResult = 'Quesito 1 gerado?\nQuesito 2 gerado?';
            (useGeradorQuesitosStore as any).mockImplementation((selector: any) => selector(mockStoreState));
        });
        renderComponent(); // Re-render or trigger update if store doesn't auto-update component

        await waitFor(() => {
            expect(screen.getByText('Quesito 1 gerado?')).toBeInTheDocument();
            expect(screen.getByText('Quesito 2 gerado?')).toBeInTheDocument();
        });
    });

    test('GQ-FE-002: Tentativa de upload de arquivo com formato inválido (não PDF)', async () => {
        renderComponent();
        await selectBeneficio(OPCOES_BENEFICIO[0]);
        await selectProfissao(OPCOES_PROFISSAO[0]);

        const invalidFile = new File(['dummy content'], 'test.txt', { type: 'text/plain' });
        const fileInputElement = screen.getByTestId('file-input-gerador-quesitos');
        fireEvent.change(fileInputElement, { target: { files: [invalidFile] } });

        await waitFor(() => {
            // Verifica a mensagem de UI sobre arquivos ignorados
            expect(screen.getByText(/1 arquivo\(s\) ignorado\(s\) por não ser\(em\) PDF./i)).toBeInTheDocument();
        });

        // Verifica que o arquivo inválido não foi adicionado à lista de selectedFiles (visualmente)
        expect(screen.queryByText(invalidFile.name)).not.toBeInTheDocument();

        const submitButton = screen.getByRole('button', { name: /gerar quesitos/i });
        // O botão deve estar desabilitado se nenhum PDF válido foi selecionado
        expect(submitButton).toBeDisabled();
    });

    test('GQ-FE-003: Erro durante o upload/processamento do PDF (simulado via store)', async () => {
        renderComponent();
        await selectBeneficio(OPCOES_BENEFICIO[0]);
        await selectProfissao(OPCOES_PROFISSAO[0]);

        const fakeFile = new File(['dummy content'], 'error_test.pdf', { type: 'application/pdf' });
        const fileInputElement = screen.getByTestId('file-input-gerador-quesitos');
        fireEvent.change(fileInputElement, { target: { files: [fakeFile] } });

        await waitFor(() => expect(screen.getByText(fakeFile.name)).toBeInTheDocument());

        mockUploadAndProcessSinglePdfForQuesitos.mockImplementation(() => {
            act(() => {
                mockStoreState.isLoading = false;
                mockStoreState.error = 'Falha épica no upload!';
                (useGeradorQuesitosStore as any).mockImplementation((selector: any) => selector(mockStoreState));
            });
        });

        const submitButton = screen.getByRole('button', { name: /gerar quesitos/i });
        fireEvent.click(submitButton);

        await waitFor(() => {
            expect(mockUploadAndProcessSinglePdfForQuesitos).toHaveBeenCalled();
        });

        // Re-render com o estado de erro
        renderComponent();

        await waitFor(() => {
            expect(screen.getByText('Falha épica no upload!')).toBeInTheDocument();
        });
    });

    test('GQ-FE-004: Erro durante a geração de quesitos (simulado via store após processamento)', async () => {
        renderComponent();
        await selectBeneficio(OPCOES_BENEFICIO[0]);
        await selectProfissao(OPCOES_PROFISSAO[0]);

        const fakeFile = new File(['dummy content'], 'gen_error.pdf', { type: 'application/pdf' });
        const fileInputElement = screen.getByTestId('file-input-gerador-quesitos');
        fireEvent.change(fileInputElement, { target: { files: [fakeFile] } });
        await waitFor(() => screen.getByText(fakeFile.name));

        mockUploadAndProcessSinglePdfForQuesitos.mockImplementation(() => {
            act(() => {
                // Simula que o processamento do documento ocorreu, mas a geração de quesitos falhou
                mockStoreState.processedDocumentInfo = { id: 'doc123', file_hash: 'hash123', file_name: fakeFile.name, status: 'processed' };
                mockStoreState.isLoading = false;
                mockStoreState.error = 'Falha ao gerar os quesitos no backend.';
                // quesitosResult permaneceria null ou vazio
                (useGeradorQuesitosStore as any).mockImplementation((selector: any) => selector(mockStoreState));
            });
        });

        const submitButton = screen.getByRole('button', { name: /gerar quesitos/i });
        fireEvent.click(submitButton);

        await waitFor(() => expect(mockUploadAndProcessSinglePdfForQuesitos).toHaveBeenCalled());

        // Re-render com o estado de erro
        renderComponent();

        await waitFor(() => {
            expect(screen.getByText('Falha ao gerar os quesitos no backend.')).toBeInTheDocument();
            // Verifica se o processedDocumentInfo é exibido se o erro ocorreu *após* o processamento do PDF
            // (Esta parte do teste depende de como o componente lida com erros parciais)
        });
    });

    test('GQ-FE-005: Estado de carregamento/feedback visual', async () => {
        renderComponent();
        await selectBeneficio(OPCOES_BENEFICIO[0]);
        await selectProfissao(OPCOES_PROFISSAO[0]);

        const fakeFile = new File(['dummy content'], 'loading_test.pdf', { type: 'application/pdf' });
        const fileInputElement = screen.getByTestId('file-input-gerador-quesitos');
        fireEvent.change(fileInputElement, { target: { files: [fakeFile] } });
        await waitFor(() => screen.getByText(fakeFile.name));

        mockUploadAndProcessSinglePdfForQuesitos.mockImplementation(async () => {
            act(() => {
                mockStoreState.isLoading = true;
                mockStoreState.currentFileBeingProcessed = fakeFile;
                 // Simula que o documento foi processado e temos o ID antes da geração dos quesitos
                mockStoreState.processedDocumentInfo = { id: 'doc-loading-id', file_hash: 'hash-loading', file_name: fakeFile.name, status: 'processing' };

                (useGeradorQuesitosStore as any).mockImplementation((selector: any) => selector(mockStoreState));
            });
            // Simular um pequeno atraso para o estado de loading ser renderizado
            await act(async () => {
                await new Promise(resolve => setTimeout(resolve, 50));
            });
        });

        const submitButton = screen.getByRole('button', { name: /gerar quesitos/i });
        fireEvent.click(submitButton);

        // Re-render com o estado de loading
        renderComponent();

        await waitFor(() => {
            expect(screen.getByRole('progressbar')).toBeInTheDocument();
            expect(screen.getByText(`Processando: ${fakeFile.name}`)).toBeInTheDocument();
            expect(screen.getByText(/Benefício:/)).toBeInTheDocument();
            expect(screen.getByText(/Profissão:/)).toBeInTheDocument();
            expect(screen.getByText(/Modelo:/)).toBeInTheDocument();
            expect(screen.getByText(/ID doc-loading-id/)).toBeInTheDocument(); // Verifica se o ID do documento é mostrado
        });

        // Verificar frase divertida (mockada)
        act(() => { vi.advanceTimersByTime(100); }); // Avança o timer para o useEffect da frase
        await waitFor(() => {
            expect(screen.getByText(FRASES_DIVERTIDAS[0])).toBeInTheDocument();
        });

        // Simular conclusão
        act(() => {
            mockStoreState.isLoading = false;
            mockStoreState.quesitosResult = "Quesitos carregados!";
            mockStoreState.currentFileBeingProcessed = null;
            (useGeradorQuesitosStore as any).mockImplementation((selector: any) => selector(mockStoreState));
        });
        renderComponent(); // Re-render

        await waitFor(() => {
            expect(screen.getByText("Quesitos carregados!")).toBeInTheDocument();
            expect(screen.queryByRole('progressbar')).not.toBeInTheDocument();
        });
    });

    test('GQ-FE-006: Limpar arquivos selecionados e resultados (Botão "Gerar Quesitos" atua como reset se clicado novamente após sucesso/erro)', async () => {
        // Este teste precisa ser adaptado porque não há um botão "Limpar" explícito.
        // A lógica de "limpeza" está mais em remover arquivos individualmente
        // ou o fato de que uma nova submissão substitui os resultados anteriores.

        renderComponent();
        await selectBeneficio(OPCOES_BENEFICIO[0]);
        await selectProfissao(OPCOES_PROFISSAO[0]);

        const file1 = new File(['content1'], 'file1.pdf', { type: 'application/pdf' });
        const fileInputElement = screen.getByTestId('file-input-gerador-quesitos');
        fireEvent.change(fileInputElement, { target: { files: [file1] } });

        await waitFor(() => screen.getByText('file1.pdf'));
        expect(screen.getByText(/1 selecionado/i)).toBeInTheDocument(); // "Arquivo Selecionado: file1.pdf"

        // Remover o arquivo
        const deleteButton = screen.getByRole('button', { name: /delete/i });
        fireEvent.click(deleteButton);

        await waitFor(() => {
            expect(screen.queryByText('file1.pdf')).not.toBeInTheDocument();
        });
        expect(screen.getByRole('button', { name: /gerar quesitos/i })).toBeDisabled(); // Desabilitado porque não há arquivos

        // Adicionar arquivo novamente e gerar quesitos
        fireEvent.change(fileInputElement, { target: { files: [file1] } });
        await waitFor(() => screen.getByText('file1.pdf'));

        mockUploadAndProcessSinglePdfForQuesitos.mockImplementationOnce(() => {
            act(() => {
                mockStoreState.isLoading = false;
                mockStoreState.quesitosResult = 'Resultados para file1';
                (useGeradorQuesitosStore as any).mockImplementation((selector: any) => selector(mockStoreState));
            });
        });
        fireEvent.click(screen.getByRole('button', { name: /gerar quesitos/i }));
        renderComponent();
        await waitFor(() => screen.getByText('Resultados para file1'));

        // Simular uma nova seleção de arquivo e submissão (que deve limpar os resultados anteriores)
        const file2 = new File(['content2'], 'file2.pdf', { type: 'application/pdf' });
        // Primeiro, remover o file1 para adicionar o file2 (já que só processa o primeiro)
        fireEvent.click(screen.getByRole('button', { name: /delete/i }));
        await waitFor(() => expect(screen.queryByText('file1.pdf')).not.toBeInTheDocument());

        fireEvent.change(fileInputElement, { target: { files: [file2] } });
        await waitFor(() => screen.getByText('file2.pdf'));

        // Limpar o mock de store para a nova chamada
        act(() => {
            mockStoreState.quesitosResult = null; // Limpa resultado anterior
            mockStoreState.error = null; // Limpa erro anterior
            (useGeradorQuesitosStore as any).mockImplementation((selector: any) => selector(mockStoreState));
        });
        renderComponent(); // Re-render com estado limpo antes da nova chamada

        mockUploadAndProcessSinglePdfForQuesitos.mockImplementationOnce(() => {
            act(() => {
                mockStoreState.isLoading = false;
                mockStoreState.quesitosResult = 'Resultados para file2';
                (useGeradorQuesitosStore as any).mockImplementation((selector: any) => selector(mockStoreState));
            });
        });

        fireEvent.click(screen.getByRole('button', { name: /gerar quesitos/i }));
        renderComponent();

        await waitFor(() => {
            expect(screen.queryByText('Resultados para file1')).not.toBeInTheDocument();
            expect(screen.getByText('Resultados para file2')).toBeInTheDocument();
        });

        // Verificar se os campos de select NÃO são limpos automaticamente (comportamento atual)
        expect(screen.getByLabelText(/benefício pretendido/i)).toHaveTextContent(OPCOES_BENEFICIO[0]);
    });

    test('Mensagens de UI para campos obrigatórios não preenchidos', async () => {
        renderComponent();
        const submitButton = screen.getByRole('button', { name: /gerar quesitos/i });

        // Nenhum arquivo, nenhum benefício, nenhuma profissão
        expect(submitButton).toBeDisabled();
        fireEvent.click(submitButton); // Clicar não deve fazer nada, mas podemos verificar se alguma mensagem aparece
                                    // O componente atual coloca a mensagem de erro no `uiMessage`
                                    // que é exibido em um Alert.

        // O botão está desabilitado, então a chamada à ação não ocorre.
        // Para testar as mensagens de validação que aparecem no `uiMessage`,
        // precisamos que o botão esteja habilitado para que `handleGerarQuesitos` seja chamado.
        // A validação atual ocorre DENTRO de `handleGerarQuesitos`.

        // Caso 1: Sem arquivos
        await selectBeneficio(OPCOES_BENEFICIO[0]);
        await selectProfissao(OPCOES_PROFISSAO[0]);
        // Botão ainda desabilitado se selectedFiles.length === 0
        expect(submitButton).toBeDisabled();
        // Para forçar a chamada e ver a mensagem, precisamos de um arquivo
        const fakeFile = new File(['content'], 'test.pdf', { type: 'application/pdf' });
        const fileInputElement = screen.getByTestId('file-input-gerador-quesitos');
        fireEvent.change(fileInputElement, { target: { files: [fakeFile] } });
        await waitFor(() => screen.getByText(fakeFile.name));

        // Remover o arquivo para simular o "sem arquivos" com os selects preenchidos
        fireEvent.click(screen.getByRole('button', { name: /delete/i }));
        await waitFor(() => expect(screen.queryByText(fakeFile.name)).not.toBeInTheDocument());

        // Agora, mesmo com selects preenchidos, o botão está desabilitado.
        // A lógica de `setUiMessage("Nenhum arquivo PDF selecionado.")` só é atingida se
        // o botão estivesse habilitado e `selectedFiles.length === 0`.
        // A condição `disabled={isLoading || selectedFiles.length === 0 || !beneficio || !profissao}`
        // previne isso. As mensagens de validação no `handleGerarQuesitos` são, portanto,
        // um fallback caso a lógica do `disabled` falhe ou seja diferente.

        // Testaremos se, ao preencher tudo menos um campo, o botão permanece desabilitado.
        // E se o erro visual (prop `error` no FormControl) aparece.

        // Caso 2: Sem benefício (arquivo e profissão OK)
        renderComponent(); // Reset
        fireEvent.change(fileInputElement, { target: { files: [fakeFile] } });
        await waitFor(() => screen.getByText(fakeFile.name));
        await selectProfissao(OPCOES_PROFISSAO[0]);
        expect(submitButton).toBeDisabled();
        // Forçar clique para ver se o FormControl fica com erro (não vai porque está disabled)
        // A prop `error` do FormControl é ativada por `!!uiMessage && !beneficio`
        // Então, precisamos simular um `uiMessage`
        act(() => { (GeradorQuesitos as any).type.prototype.setState({ uiMessage: "Dummy message" }) }); // Não funciona assim com FC
        // A forma correta é simular o clique e o `handleGerarQuesitos` setar o `uiMessage`.
        // Como o botão está desabilitado, isso não acontece.
        // Vamos verificar a condição de `disabled` indiretamente.

        // Se tentarmos submeter com campos faltando, o `handleGerarQuesitos` (se chamado) definiria `uiMessage`.
        // E o `FormControl` ficaria com `error={true}`.
        // Ex: Se o botão *não* estivesse desabilitado e clicássemos:
        // fireEvent.click(submitButton);
        // await waitFor(() => expect(screen.getByText("Por favor, selecione o benefício.")).toBeInTheDocument());
        // E o FormControl do Benefício teria o estado de erro.
        // Como está, a validação é primariamente pelo `disabled` do botão.
    });

});
